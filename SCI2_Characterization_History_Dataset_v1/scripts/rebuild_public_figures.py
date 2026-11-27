#!/usr/bin/env python3
"""Rebuild figure exports without ngspice. No source file mutations and no overwrites."""
import argparse, pathlib, shutil, tempfile, sys
P=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
a=parser.parse_args();out=pathlib.Path(a.output).expanduser().resolve()
if out.exists():raise SystemExit('FAIL_CLOSED: output directory already exists')
out.mkdir(parents=True)
S=out/'sources';S.mkdir()
for name in ('fig_inputs','electronic','netlist','code','evidence'):(S/name).mkdir()
shutil.copytree(P/'data/figure_inputs',S/'fig_inputs',dirs_exist_ok=True)
shutil.copytree(P/'data/electronic',S/'electronic',dirs_exist_ok=True)
shutil.copy(P/'data/netlists/SCI2_96_topology_netlists_only.zip',S/'netlist/frozen_topology_only.zip')
shutil.copytree(P/'scripts/code',S/'code',dirs_exist_ok=True)
shutil.copy(P/'reproduction_sources/evidence/C1_fresh.json',S/'evidence/C1_fresh.json')
sys.path.insert(0,str(P/'scripts'))
from build_figures import build
build(out,S)
print('FIGURE_REBUILD_COMPLETED=8', out/'03_FIGURES')
