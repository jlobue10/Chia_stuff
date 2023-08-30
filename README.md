# Chia_stuff
Helpful automation stuff for Chia plot creation. Fill up a staging directory with new `bladebit_cuda` plots as room frees up.

## **Installation**

I thought I'd share my automation technique for filling the staging drive as the [Plow](https://github.com/lmacken/plow) does its job.

Some manual edits to the 3 files will be necessary to get your desired result, but hopefully these are fairly straightforward.

```
git clone https://github.com/jlobue10/Chia_stuff
cd Chia_stuff
# Make edits to timer and service before installing in /etc/systemd/system
sudo cp {bladebit_check_and_plot.timer,bladebit_check_and_plot.service} /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable --now bladebit_check_and_plot.timer
sudo systemctl status bladebit_check_and_plot.timer
# should see that timer enabled and active
```

Feel free to ask questions as necessary. There are more [elegant solutions](https://github.com/graemes/mownplow) out there, but documentation can be somewhat lacking if you're not experienced in Python, so I came up with this more 'crude' `bash` and `systemd` solution.
