import os

from main import target_subfolder

assert target_subfolder("wn123_run.csv") == "WN123"
assert target_subfolder("G400Plus-07.csv") == os.path.join("G400+", "G400+-07")
assert target_subfolder("g+-12 data.txt") == os.path.join("G400+", "G400+-12")
assert target_subfolder("random.csv") is None
print("ok")
