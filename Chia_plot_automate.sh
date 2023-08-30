#!/usr/bin/bash

# Change C0 to C7 for C1 to C7
# Uncomment and comment out as necessary for desired C level
#COMPRESS_LEVEL=C0
#COMPRESS_LEVEL=C1
#COMPRESS_LEVEL=C2
#COMPRESS_LEVEL=C3
#COMPRESS_LEVEL=C4
#COMPRESS_LEVEL=C5
#COMPRESS_LEVEL=C6
COMPRESS_LEVEL=C7

# Fill in your Farmer Public Key and Pool Contract Address
FARMER_KEY=REPLACE_WITH_YOUR_FARMER_PUBLIC_KEY
CONTRACT_ADDR=REPLACE_WITH_YOUR_POOL_CONTRACT_ADDRESS

# Change to your plot directory where you want bladebit to make new plots
# PLOT_DIR=$HOME
# Example:
# PLOT_DIR=/mnt/Chia_JBOD001/Chia_plots
PLOT_DIR=REPLACE_WITH_YOUR_DEST_DIR_FOR_NEW_BLADEBIT_PLOTS

if [[ "$COMPRESS_LEVEL" == "C0" ]]; then
	reqSpace=108770000
	COMPRESS_VALUE=0
	# 108.77GB
fi

if [[ "$COMPRESS_LEVEL" == "C1" ]]; then
	reqSpace=93990000
	COMPRESS_VALUE=1
	# 93.99GB
fi

if [[ "$COMPRESS_LEVEL" == "C2" ]]; then
	reqSpace=92370000
	COMPRESS_VALUE=2
	# 92.37GB
fi

if [[ "$COMPRESS_LEVEL" == "C3" ]]; then
	reqSpace=90690000
	COMPRESS_VALUE=3
	# 90.69GB
fi

if [[ "$COMPRESS_LEVEL" == "C4" ]]; then
	reqSpace=88970000
	COMPRESS_VALUE=4
	# 88.97GB
fi

if [[ "$COMPRESS_LEVEL" == "C5" ]]; then
	reqSpace=87250000
	COMPRESS_VALUE=5
	# 87.25GB
fi

if [[ "$COMPRESS_LEVEL" == "C6" ]]; then
	reqSpace=85520000
	COMPRESS_VALUE=6
	# 85.52GB
fi

if [[ "$COMPRESS_LEVEL" == "C7" ]]; then
	reqSpace=83810000
	COMPRESS_VALUE=7
	# 83.81GB
fi

AVAIL_PLOT_SPACE=`df "$PLOT_DIR" | awk 'END{print $4}'`
if [[ $AVAIL_PLOT_SPACE -ge reqSpace ]]; then
    /usr/bin/env PATH=/$HOME/chia-blockchain/venv/bin:$PATH bladebit_cuda -f $FARMER_KEY -c $CONTRACT_ADDR -n 1 --compress $COMPRESS_VALUE cudaplot $PLOT_DIR
    # ^ assuming that user has cloned repo to their $HOME dir and done the install steps following clone
    # Fix Python venv location as necessary. Replace $HOME with /home/user as necessary
    exit 0
fi
