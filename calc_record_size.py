# Calculate actual record size from payload evidence

# Record 1 NumSlotsElapsed found at absolute offset 96 in payload
# NumSlotsElapsed is at offset 4 within a record
rec1_start = 96 - 4
print(f'Record 1 starts at payload offset: {rec1_start}')

# Record 0 should start after header (version 4 bytes + header fields ~12 bytes = ~16)
rec0_start = 16
record_size = rec1_start - rec0_start
print(f'Record 0 starts at offset: {rec0_start}')
print(f'Calculated record size: {record_size} bytes')

payload_size = 163
available = payload_size - rec0_start
max_recs = available // record_size
print(f'Available bytes: {available}')
print(f'Max complete records: {max_recs}')
print(f'Bytes for {max_recs} records: {max_recs * record_size}')

remaining = available - (max_recs * record_size)
print(f'Remaining bytes: {remaining}')
print()

# Check if Record 2 would fit
rec2_start = rec1_start + record_size
print(f'Record 2 would start at offset: {rec2_start}')
print(f'Record 2 would end at offset: {rec2_start + record_size}')
print(f'Payload ends at offset: {payload_size}')

if rec2_start + record_size <= payload_size:
    print('Record 2 would FIT')
else:
    print('Record 2 would NOT fit completely')
    partial_bytes = payload_size - rec2_start
    print(f'Only {partial_bytes} bytes available for Record 2')
