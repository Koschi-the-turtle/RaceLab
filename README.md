#  RaceLab

RaceLab is a python program which allows you to create your own custom maps and tracks, test them, and even train AIs to drive on them !

# Notice:
If you simply want to demo test this, especially for the AI training, I recommend you use the map I made as it has shown correct results over numerous tests.
To do that, simply download the json file, and while in editor mode in the main program, press Enter and load the json file, then press T to start the training and wait like 10-15 minutes for it to finish.

# Map Editor

https://github.com/user-attachments/assets/7c2763dd-dc6d-4799-81dd-9803363d88a2

The editor mode is the default mode for when you open the game. The menu on the bottom of your screen gives you access to 5 different tools:

- Walls -> lets you place walls (suprising I know), btw it uses the Bresenham line algorithm to draw continuous lines instead of a series of point
- Spawn -> yeah I think you can already tell what it does
- Finish -> yes it places finish points, but also quick notice, you can place it on the spawn point, which will put the game into loop mode (by default in point-to-point),
meaning that when you'll drive, the game will continue even after you reach the finish line so you can drive in a loop infintely
- Checkpoint -> places checkpoints which will have to be reached in the same order you placed them, it's "rank" is written on it so you know what order it's currently in
- Erase -> yeah pretty straight forward it just erases stuff, btw you can also just erase using your mouse right-click, it's more practical than to switch tool all the time

Things you should be aware of when making your map:

 - The car is slightly under 2 cells long and a bit over 1 cell wide, so you should take that into account and make the track quite wide (at least 5 cells wide, make it 7 or 8 to be comfortable)
 - don't put spawn points / finish points / checkpoints to far apart, their is a fixed time limit for which the AI must reach the next checkpoint, so if it's too far it won't reach it
 - Don't forget to put walls, yeah I know it seems supid but genuinely, when they are no walls, even if the finish line is just 10 cells forward the AI freaks out and drives in circle idk bro just make a clean track
 - I recommend you test your track yourself before training the AI on it just to be sure it's clean and all
 - Oh and also btw you can Ctrl - Z if you want

To close the game, press Esc
To switch to driving mode, just press Tab

# Driving

https://github.com/user-attachments/assets/168116d5-4aff-4816-bdd5-ea10224dabb3

When pressing tab, you will first get a pop up to choose which car you want to drive (they're all the same it's just visual), then by presing Enter (or Tab for some reason)
you will go into driving more, with your selected car. 

To drive, you can either use WASD or the arrow keys.

I don't think you need to know anything else about driving, maybe just try not to hit walls, and yeah it seems logical, but it's actually because the collisions are still
a bit messed up so you can get stuck and I mean really stuck sometimes.

Oh I almost forgot but when you get your fastest time, for both sector time and lap time, the time turns purple. When it's better than the last lap, it's green, and if worse it's red.
Just a simple color system from IRL racing to give you a bit more information about your performances.

If you want to go back to editor mode, just press Tab

# AI Training

https://github.com/user-attachments/assets/b7e0f311-1e1d-413d-8a29-0cf7411b8ca5

To start the AI training, press T

For your information, the game window might not react for a while, until the first generation finishes training, then you'll see the training menu.
you'll see the generation's fintess as well as a "watch" button on the side, don't press it until all generations are finished so after the training is complete.
Then you can watch each generation's best run and compare their performance.

Currently the AI tranining is set to 50 generations with a population of 200 cars, from which the 25 best will be kept to create the other generations of AI, while mutating each a little at a rate of 0.15.

# JSON Map export/import

While in editor mode, you can export or import a map at any time. Just press Enter, and a popup will appear. Select export to convert your current map to a Json file, or select import to load an already finished map from your file explorer.

https://github.com/user-attachments/assets/dcc29397-f018-4250-b9c2-8eb69c1e6ca5


