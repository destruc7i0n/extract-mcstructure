# extract-mcstructure

Extract's mcstructures from the Bedrock leveldb (possibly saved from the `/structure` command) to `.mcstructure` files which can be moved across worlds.

## Usage

`python3 run.py World all` - Extracts all mcstructures from the world named "World" (as seen on the in-game menu)

`python3 run.py World house` - Extracts the structure named "house" from the world named "World"

All extracted files will be outputted to a `structures` folder in the world folder. 

Periods in the namespace will automatically create subdirectories in the `structures` folder. 
Ex: `destruc7i0n.test:structure` will output to `<world>/structures/destruc7i0n/test/structure.mcstructure`

### Note
`leveldb` lib is from `Amulet-Team/Amulet-Core`.
