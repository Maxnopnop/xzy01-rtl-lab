"""Predeclared observable associations, never internal-cognition claims."""
def classify(a,b,c):
    if c=='NOT_ASSESSABLE':return 'NOT_ASSESSABLE'
    if a==b==c=='PASS':return 'ALL_MATCH'
    if a=='PASS' and b!='PASS' and c!='PASS':return 'RTL_IMPLEMENTATION_DIVERGENCE'
    if a!='PASS' and b!='PASS' and c=='PASS':return 'IR_SPEC_DIVERGENCE_RTL_FOLLOWS_IR'
    if a!='PASS' and b=='PASS' and c!='PASS':return 'RTL_CORRECT_DESPITE_IR_DIVERGENCE'
    if a!='PASS' and b!='PASS' and c!='PASS':return 'BOTH_DIVERGE_UNATTRIBUTED'
    if a==b=='PASS' and c!='PASS':return 'REFERENCE_OR_ALIGNMENT_CONFLICT'
    return 'OBSERVABLE_DIVERGENCE'
