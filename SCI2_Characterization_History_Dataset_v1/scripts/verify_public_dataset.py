#!/usr/bin/env python3
"""Public SCI2 dataset: integrity + core scientific count checks (stdlib)."""
import hashlib,csv,pathlib,collections,math
P=pathlib.Path(__file__).resolve().parents[1]
lines=(P/'SHA256SUMS.txt').read_text(encoding='utf8').splitlines()
for line in lines:
 expected,rel=line.split('  ',1); file=P/rel
 if not file.is_file():raise SystemExit('MISSING '+rel)
 h=hashlib.sha256(file.read_bytes()).hexdigest()
 if h!=expected:raise SystemExit('HASH_FAIL '+rel)
print('HASHES=PASS',len(lines))
def rows(n):
 with (P/'data/electronic'/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
want={'Supplementary_Data_S5_D.csv':544,'Supplementary_Data_S5_E.csv':544,'Supplementary_Data_S5_F_C1_K1_K4.csv':4,'Supplementary_Data_S6_D.csv':56,'Supplementary_Data_S6_E.csv':96,'Supplementary_Data_S7_D.csv':80,'Supplementary_Data_S8_D.csv':4032,'Supplementary_Data_S8_E.csv':480,'Supplementary_Data_S8_F.csv':240,'Supplementary_Data_S9_A.csv':8,'Supplementary_Data_S9_B.csv':20,'Supplementary_Data_S9_C.csv':6,'Supplementary_Data_S9_D.csv':4,'Supplementary_Data_S9_F.csv':8,'Supplementary_Data_S9_per_config_edge.csv':384,'Supplementary_Data_S10_A.csv':48,'Supplementary_Data_S10_B.csv':16,'Supplementary_Data_S11_C.csv':36,'Supplementary_Data_S11_D.csv':216}
for n,num in want.items():
 r=rows(n)
 if len(r)!=num:raise SystemExit(f'ROWS_FAIL {n} {len(r)} != {num}')
print('CANONICAL_CSV=PASS',len(want),'rows',sum(want.values()))
r=rows('Supplementary_Data_S8_E.csv')
def mae(m):return sum(abs(float(x[m])-float(x['ref'])) for x in r)/len(r)
def passed(m):return sum((abs(float(x[m])-float(x['ref']))<=5.0) and (abs(float(x[m])-float(x['ref']))<=0.05*abs(float(x['ref']))) for x in r)
for model,num in [('P0',441),('P_IS1',467),('P_R2',478),('P_IS2',480)]:
 p=passed(model)
 if p!=num:raise SystemExit(f'PASSCOUNT_FAIL {model}: {p}')
print('TABLEIII_REPLAY=PASS', ' '.join(f'{m}={mae(m):.6f}fs({passed(m)}/480)' for m in ['P0','P_IS1','P_R2','P_IS2']))
m5=rows('Supplementary_Data_S10_B.csv')
for condition in ('LOAD_FO2_PERSTAGE','LOAD_FO4_PERSTAGE'):
 p=sum(row['primary_pass'].lower()=='true' for row in m5 if row['condition']==condition and row['edge']=='td_phl')
 if p!=4:raise SystemExit(f'M5_FAIL {condition} {p}/4')
print('M5=PASS_4_4_FO2_AND_FO4')
s11=rows('Supplementary_Data_S11_C.csv')
assert len(s11)==36
for row in s11:
 assert row['ordered_DC_ISL_ISS']=='True' and row['periodic']=='True'
 assert float(row['s_DC'])>=float(row['s_ISL'])>=float(row['s_ISS'])
print('S11=PASS_36/36; S11_readings=216')
print('DATASET_VERIFY=PASS; NO_SIMULATION=TRUE')
