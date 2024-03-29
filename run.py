import os, sys
import typing
import argparse
from pathlib import Path

import amulet_nbt
from leveldb import LevelDB

StructureDict = typing.Dict[str, amulet_nbt.NamedTag]

parser = argparse.ArgumentParser(
  description='Extract .mcstructure files'
)
parser.add_argument('world_name', type=str, help='the world name as appears in the game')
parser.add_argument('structure_id', type=str, help='the structure id or "all" to export all')
parser.add_argument('--behavior-pack', default=False, action='store_true', help='save to the first behavior pack in the world')
parser.add_argument('--force', default=False, action='store_true', help='force save the structure file')
parser.add_argument('--delete', default=False, action='store_true', help='delete structures')

# adapted from https://github.com/minecraft-addon-tools/minecraft-addon-toolchain/blob/master/packages/minecraft-addon-toolchain/v1/index.js#L65-L94
PATH_LOCATIONS = {
  'win32': os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState"),
  'darwin': os.path.join(Path.home(), 'Library/Application Support/mcpelauncher'),
  'linux': os.path.join(Path.home(), '.local/share/mcpelauncher'),
  'android': os.path.join(Path.home(), 'storage/shared/')
}

def get_worlds_folder() -> str:
  worlds_folder = PATH_LOCATIONS[sys.platform]

  if not worlds_folder:
    print('Unsupported platform!')
    exit(1)
  elif not Path(worlds_folder).exists():
    print('Could not find Minecraft Worlds folder!')
    exit(1)
  
  worlds_folder = os.path.join(worlds_folder, 'games/com.mojang/minecraftWorlds')
  return worlds_folder

def save_structures (dir: str, structures: StructureDict, force: bool) -> None:
  for structure_id, nbt in structures.items():
    ns_id, name = structure_id.split(':')
    namespace, *rest = ns_id.split('.')

    folder = '/'.join(rest)

    if not namespace: namespace = 'mystructure'

    file_name = name + '.mcstructure'
    
    path = Path(os.path.join(dir, 'structures', namespace, folder))
    path.mkdir(parents=True, exist_ok=True) # ensure exists
    
    path = path.joinpath(file_name)

    structure_load_id = f'{namespace}:{name}'
    if len(folder) > 0:
      structure_load_id = f'{namespace}:{folder}/{name}'

    # print(nbt.to_snbt())

    if path.exists() and not force:
      print(f'Structure file already exists for "{file_name}" at {structure_load_id}! Try saving as a different structure name. Skipping file.')
    else:
      print(f'Saved "{structure_id}" to {structure_load_id}')
      with open(path, 'wb') as f: nbt.save_to(filepath_or_buffer=f, little_endian=True, compressed=False)

def get_world_paths() -> typing.Dict[str, str]:
  name_to_path = {}

  for file in os.scandir(get_worlds_folder()):
    if file.is_dir():
      world_name_path = os.path.join(file.path, 'levelname.txt')
      if os.path.exists(world_name_path):
        with open(world_name_path, 'r') as f: name_to_path[f.readline()] = file.path

  return name_to_path

def main():
  args = parser.parse_args()

  world_paths = get_world_paths()

  if args.world_name not in world_paths:
    print(f'Could not find world by the name of "{args.world_name}"')
    exit(1)

  world_path = world_paths[args.world_name]

  output_folder = world_path
  if args.behavior_pack:
    behavior_packs_path = os.path.join(world_path, 'behavior_packs')
    behavior_pack = [ file.path for file in os.scandir(behavior_packs_path) if file.is_dir() ][0]
    if not behavior_pack: 
      print('Could not find behavior pack!')
      exit(1)
    else:
      output_folder = behavior_pack

  db_path = os.path.join(world_path, 'db')
  db = LevelDB(db_path)

  structures: StructureDict = {}

  structure_id = args.structure_id
  if structure_id != 'all':
    if ':' not in structure_id: structure_id = 'mystructure:' + structure_id

  for key, data in db.iterate():
    try:
      key_str = key.decode('ascii')
      if key_str.startswith('structuretemplate_'):
        str_id = key_str[len('structuretemplate_'):]

        structure = amulet_nbt.load(filepath_or_buffer=data, little_endian=True)
        structures[str_id] = structure

        if (str_id == structure_id or structure_id == 'all') and args.delete:
          # print(f'Deleted structure "{str_id}" from the leveldb database')
          db.delete(key)
    except: pass

  db.close()

  filtered_structures = {}
  if structure_id != 'all':
    if structure_id not in structures:
      print(f'Could not find structure with the id of "{structure_id}"! Available ids: {", ".join(structures.keys())}')
      exit(0)
      
    filtered_structures = { key: value for key, value in structures.items() if key == structure_id }
  elif structure_id == 'all':
    filtered_structures = structures

  if len(filtered_structures) == 0:
    print(f'No structures found!')
    exit(0)
  else:
    print(f'Preparing to save {", ".join(filtered_structures.keys())}')
  
  save_structures(output_folder, filtered_structures, args.force)

if __name__ == '__main__': main()
