https://pixelartmaker.com/offshoot/9020b04ca9f4509

Want objects to take the shortest path to the lander.
So instead of facing the lander, they should face the closest of three points - lander coords,
lander coords - world width, lander coords + world width
Also, make sure, like the lander, that they do wrap around!!

should use spatial hashing on ground enemies

Make certain that there is a spot for the landing pad.
Easy to do - make it the first rect in the central terrain, then swap it with another rect.

