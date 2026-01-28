# Report Refactor Progress

| Report File | Has AQL Query | Refactored |
|-------------|--------------|------------|
| Report0002.py | Yes | Yes |
| Report0003.py | Yes | Yes |
| Report0004.py | Yes | Yes |
| Report0005.py | Yes | Yes |
| Report0006.py | Yes | Yes |
| Report0007.py | Yes | Yes |
| Report0009.py | Yes | Yes |
| Report0010.py | Yes | Yes |
| Report0012.py | Yes | Yes |
| Report0013.py | Yes | Yes |
| Report0014.py | Yes | Yes |
| Report0015.py | Yes | Yes |
| Report0016.py | Yes | Yes |
| Report0017.py | Yes | Yes |
| Report0018.py | Yes | Yes |
| Report0019.py | Yes | Yes |
| Report0020.py | Yes | Yes |
| Report0023.py | Yes | Yes |
| Report0024.py | Yes | Yes |
| Report0025.py | Yes | Yes |
| Report0026.py | Yes | Yes |
| Report0032.py | Yes | Yes |
| Report0033.py | Yes | Yes |
| Report0034.py | Yes | Yes |
| Report0035.py | Yes | No |
| Report0037.py | Yes | Yes |
| Report0038.py | Yes | Yes |
| Report0040.py | Yes | Yes |
| Report0041.py | Yes | Yes |
| Report0042.py | Yes | Yes |
| Report0045.py | Yes | Yes |
| Report0046.py | Yes | Yes |
| Report0058.py | Yes | Yes |
| Report0059.py | Yes | Yes |
| Report0060.py | Yes | Yes |
| Report0061.py | Yes | Yes |
| Report0075.py | Yes | Yes |
| Report0078.py | Yes | Yes |
| Report0079.py | Yes | Yes |
| Report0080.py | Yes | Yes |
| Report0081.py | Yes | Yes |
| Report0082.py | Yes | Yes |
| Report0083.py | Yes | Yes |
| Report0085.py | Yes | Yes |
| Report0086.py | Yes | Yes |
| Report0087.py | Yes | Yes |
| Report0088.py | Yes | Yes |
| Report0089.py | Yes | Yes |
| Report0090.py | Yes | Yes |
| Report0091.py | Yes | Yes |
| Report0092.py | Yes | Yes |
| Report0093.py | Yes | Yes |
| Report0094.py | Yes | Yes |
| Report0095.py | Yes | Yes |
| Report0096.py | Yes | Yes |
| Report0097.py | Yes | Yes |
| Report0098.py | Yes | Yes |
| Report0099.py | Yes | Yes |
| Report0100.py | Yes | Yes |
| Report0111.py | Yes | Yes |
| Report0112.py | Yes | Yes |
| Report0116.py | Yes | Yes |
| Report0119.py | Yes | Yes |
| Report0124.py | Yes | Yes |
| Report0125.py | Yes | Yes |
| Report0126.py | Yes | Yes |
| Report0127.py | Yes | Yes |
| Report0132.py | Yes | Yes |
| Report0155.py | Yes | Yes |
| Report0217.py | Yes | Yes |
| Report0218.py | Yes | Yes |

# Notes
- Files with only documentation comments about AQL (not actual queries) are not included.
- All reports with AQL queries are now listed. Refactor status is 'No' for newly found reports unless already refactored.
- Report0043 is PostGIS-based and not refactored to AQL. Skipped for now because it dynamically builds its query using PostGIS and OTL, not a static AQL report. Porting would require a full rewrite and more context.
