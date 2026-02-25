Scripts
=======

Use `./generateDataFiles.py` to collect unit, building and tech stats such as costs
from the dat files using `genieutils-py`,
the descriptive strings from a key-value-strings-utf8.txt file from aoe2de,
and the tech tree data from the civTechTrees.json file from aoe2de.

Create and activate a virtual environment with genieutils-py installed:

```sh
python -m venv .env && source .env/bin/activate && pip install genieutils-py
```

```sh
python -m venv .env && source .env/bin/activate.fish && pip install genieutils-py
```

Example invocation:

```sh
python generateBuildingTechUnitImages.py ~/.steam/steam/steamapps/common/AoE2DE
python generateDataFiles.py ~/.steam/steam/steamapps/common/AoE2DE
python generateTechTreeJsons.py ~/.steam/steam/steamapps/common/AoE2DE
```
