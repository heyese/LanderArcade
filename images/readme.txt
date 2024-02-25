https://pixelartmaker.com/offshoot/9020b04ca9f4509

Building an .exe:
~/PycharmProjects/LanderArcade
$ python -m nuitka --onefile main.py --include-data-dir=images=images --windows-icon-from-ico=images/lander.png --disable-console
So far, single file doesn't seem to work when moved to a new directory?

When the shield gets 'trapped', perhaps the simplest thing is to manually
move upwards?  At least, I should think about this problem explicitly


Add an enemy aircraft
Have a "super missile launcher"
Want explosions to exert force

Update the game readme

