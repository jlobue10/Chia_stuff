#!/usr/bin/env python3
"""
The Plow.

An efficient Chia plot mover.

Author: Luke Macken <phorex@protonmail.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import sys
import glob
import shutil
import random
import urllib.request
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Local plot sources
# For wildcards:
#   SOURCES = glob.glob('/mnt/*')
SOURCES = ["/mnt/Chia_RAID0/Chia_plots/"]

# Rsync destinations
# Examples: 
#   DESTS = ["/mnt/HDD1", "/mnt/HDD2", "192.168.1.10::hdd1"]
DESTS = ["/mnt/Chia_JBOD2_018/Chia_plots", "/mnt/Chia_JBOD2_019/Chia_plots", "/mnt/Chia_JBOD2_020/Chia_plots", "/mnt/Chia_JBOD2_021/Chia_plots"]

# Shuffle plot destinations. Useful when using many plotters to decrease the odds
# of them copying to the same drive simultaneously.
SHUFFLE = False

# Rsync bandwidth limiting
BWLIMIT = None

# Optionally set the I/O scheduling class and priority
IONICE = "-c 2 -n 0"  # "-c 3" for "idle"

# Only send 1 plot at a time, regardless of source/dest. 
ONE_AT_A_TIME = False

# Each plot source can have a lock, so we don't send more than one file from
# that origin at any given time.
ONE_PER_DRIVE = False

# Delete only plots older than this number of days
DAYS_THRESHOLD = 90  

# Keep this many times the plot size free on the destination drive as buffer
# to minimize file fragmentation and improve performance.
FREE_SPACE_MULTIPLIER = 3

# Extension of the new plot files being created
PLOT_EXT = ".plot"

# Short & long sleep durations upon various error conditions
SLEEP_FOR = 60 * 3
SLEEP_FOR_LONG = 60 * 20

RSYNC_CMD = "rsync"
processed_files = set()

if SHUFFLE:
    random.shuffle(DESTS)

# Rsync parameters. For FAT/NTFS you may need to remove --preallocate
if BWLIMIT:
    RSYNC_FLAGS = f"--remove-source-files --whole-file --bwlimit={BWLIMIT}"
else:
    RSYNC_FLAGS = "--remove-source-files --whole-file --progress"

if IONICE:
    RSYNC_CMD = f"ionice {IONICE} {RSYNC_CMD}"

LOCK = asyncio.Lock()  # Global ONE_AT_A_TIME lock
SRC_LOCKS = defaultdict(asyncio.Lock)  # ONE_PER_DRIVE locks

async def delete_file_older_than(directory, days, size):
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=days)
    dest_free = shutil.disk_usage(directory).free
    free_space_target = size * FREE_SPACE_MULTIPLIER
    freed_space = 0

    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        print("No files found in the directory.")
        return False

    for file in files:
        file_path = os.path.join(directory, file)
        modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

        # Delete files that meet the age criteria until enough space is freed up
        if modified_time < cutoff_time and (dest_free + freed_space) < free_space_target:
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)                    
                freed_space += file_size
                print(f"🔥 Slashed-and-burned: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
                return False
    
    dest_free += freed_space
    print(f"🍂 Deleted {round(freed_space/(1024*1024*1024),1)} GB from {directory} [Free space: {round((dest_free)/(1024*1024*1024),1)} GB]")

    if dest_free > size:
        return True
    else:
        return False

async def plotfinder(paths, plot_queue, loop):
    for path in paths:
        for plot in Path(path).glob("**/*" + PLOT_EXT):
            if plot not in processed_files:
                await plot_queue.put(plot)
                processed_files.add(plot)
        await watch_directory(paths, plot_queue)

async def watch_directory(paths, plot_queue):
    # Create a set to keep track of processed files
    for path in paths:
        if not Path(path).exists():
            print(f'! Path does not exist: {path}')
            continue
        while True:
            try:
                # List all files in the directory
                files = os.listdir(path)
                file_path = ""
                for file in files:
                    if file.endswith(PLOT_EXT):
                        file_path = os.path.join(path, file)

                    # Check if the file is new and not processed
                    if os.path.isfile(file_path) and file_path not in processed_files:
                        # Add the new file to the queue
                        await plot_queue.put(file_path)
                        processed_files.add(file_path)
                        print(f"🍃 Added {file} to the plot queue")

                await asyncio.sleep(60)  # Check for new files every 60 seconds
            except Exception as e:
                print(f"Error: {e}")

async def plow(dest, plot_queue, loop):
    print(f"🧑‍🌾 Plowing to {dest}")
    while True:
        try:
            plot = await plot_queue.get()
            cmd = f"{RSYNC_CMD} {RSYNC_FLAGS} {plot} {dest}"

            # For local copies, we can check if there is enough space.
            dest_path = Path(dest)
            if dest_path.exists():
                plot_size = os.path.getsize(plot)
                dest_free = shutil.disk_usage(dest).free
                if dest_free < (plot_size * FREE_SPACE_MULTIPLIER):
                    dest_space_avail = await delete_file_older_than(dest, DAYS_THRESHOLD, plot_size)
                    if dest_space_avail == False:
                        print(f"Farm {dest} is full")
                        await plot_queue.put(plot)
                        # Just quit the worker entirely for this destination.
                        break

            # One at a time, system-wide lock
            if ONE_AT_A_TIME:
                await LOCK.acquire()

            # Only send one plot from each SSD at a time
            if ONE_PER_DRIVE:
                await SRC_LOCKS[plot.parent].acquire()

            try:
                print(f"🚜 {plot} ➡️  {dest}")

                # Send a quick test copy to make sure we can write, or fail early.
                test_cmd = f"rsync /etc/hostname {dest}"
                proc = await asyncio.create_subprocess_shell(
                    test_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    print(f"⁉️  {test_cmd!r} exited with {proc.returncode}")
                    await plot_queue.put(plot)
                    break

                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                start = datetime.now()
                stdout, stderr = await proc.communicate()
                finish = datetime.now()
            finally:
                if ONE_PER_DRIVE:
                    SRC_LOCKS[plot.parent].release()
                if ONE_AT_A_TIME:
                    LOCK.release()

            if proc.returncode == 0:
                print(f"🏁 {cmd} ({finish - start})")
            elif proc.returncode == 10:  # Error in socket I/O
                # Retry later.
                print(f"⁉️ {cmd!r} exited with {proc.returncode} (error in socket I/O)")
                await plot_queue.put(plot)
                await asyncio.sleep(SLEEP_FOR_LONG)
            elif proc.returncode in (11, 23):  # Error in file I/O
                # Most likely a full drive.
                print(f"⁉️ {cmd!r} exited with {proc.returncode} (error in file I/O)")
                await plot_queue.put(plot)
                print(f"{dest} plow exiting")
                break
            else:
                print(f"⁉️ {cmd!r} exited with {proc.returncode}")
                await asyncio.sleep(SLEEP_FOR)
                await plot_queue.put(plot)
                print(f"{dest} plow exiting")
                break
            if stdout:
                output = stdout.decode().strip()
                if output:
                    print(f"{stdout.decode()}")
            if stderr:
                print(f"⁉️ {stderr.decode()}")
        except Exception as e:
            print(f"! {e}")

async def main(paths, loop):
    plot_queue = asyncio.Queue()
    futures = []

    # Add plots to queue
    futures.append(plotfinder(paths, plot_queue, loop))

    # Fire up a worker for each plow
    for dest in DESTS:
        futures.append(plow(dest, plot_queue, loop))

    print('🌱 Plow running...')
    await asyncio.gather(*futures)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(SOURCES, loop))
    except KeyboardInterrupt:
        pass
