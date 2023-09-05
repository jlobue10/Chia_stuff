# Chia_stuff
Helpful automation stuff for Chia plot creation. Fill up a staging directory with new `bladebit_cuda` plots as room frees up.

## **Installation**

I thought I'd share my automation technique for filling the staging drive as the [Plow](https://github.com/lmacken/plow) does its job.

Some manual edits to the 3 files will be necessary to get your desired result, but hopefully these are fairly straightforward.

```
git clone https://github.com/jlobue10/Chia_stuff
cd Chia_stuff
# Make edits to timer and service before installing in /etc/systemd/system
# Make edits to Chia_plot_automate.sh and copy to desired location for service to run. For me this was in $HOME/.local/chia
sudo cp {bladebit_check_and_plot.timer,bladebit_check_and_plot.service} /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable --now bladebit_check_and_plot.timer
sudo systemctl status bladebit_check_and_plot.timer
# should see that timer enabled and active
```

## **Updates**

I've added my version of the modified plow (all credit goes to original author, Luke Macken) which is deleting one older (than 90 days, can be changed in the code) plot before replacing with a new (compressed) plot. Edit as necessary and execute with `python3.9 plow.py`. You may need to install `python3.9` as an `altinstall` for your system. Newer versions of Python had some issues with the script and it's not worth re-writing (to me at least) when `python3.9` works just fine with it.

I've also added an example Chia harvesting service to be used with Linux as a `systemd` service. Edit as necessary and use if you like.
I have a Windows PowerShell harvesting and status script that I set task scheduler to launch every Windows boot. I will share this later, when I have time, for those who'd be interested in it.

Feel free to ask questions as necessary. There are more [elegant solutions](https://github.com/graemes/mownplow) out there, but documentation can be somewhat lacking if you're not experienced in Python, so I came up with this more 'crude' `bash` and `systemd` solution.
