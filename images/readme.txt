https://pixelartmaker.com/offshoot/9020b04ca9f4509

Building an .exe:
~/PycharmProjects/LanderArcade
$ python -m nuitka --onefile main.py --include-data-dir=images=images --windows-icon-from-ico=images/lander.png


When the shield gets 'trapped', perhaps the simplest thing is to manually
move upwards?  At least, I should think about this problem explicitly

Make sure I don't have clashes with where the ground objects are placed

Have levels get progressively more difficult

Add an enemy aircraft

I need something in the background when you're not in space, otherwise it's hard to tell if you're going
anywhere without looking at the minimap.