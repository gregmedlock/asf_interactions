#This script written December 2015 - January 2016, by Kevin Seitter

# Change the file path to point to the raw HEX output text file you want to analyze:
filepath = "./platefile_20171215.TXT"


#The output of the file will be [filename].xls, in the same path as the file being anaylzed

import time
import math
import numpy
import xlwt

NUM_RESISTORS = 1

timestamps = []
temps = []
data_raw = []
data_od = []
blanks = []

for i in range(NUM_RESISTORS):
	timestamps.append([])
	temps.append([])
	data_raw.append([])
	data_od.append([])
	blanks.append([])



print("Reading temperature...")
f = open(filepath,'r')
for i,l in enumerate(f):
	line = l
	timestamp = int(line[0:8],16)
	resistor = int(line[8:10],16)
	temperature = float(int(line[10:14],16))/16.0
	
	timestamps[resistor].append(timestamp)
	temps[resistor].append(temperature)
	rawdata = []
	for w in range(96):
		wellReadingHex = line[14+w*6:20+w*6]
		rawdata.append(int(wellReadingHex,16))
	data_raw[resistor].append(rawdata)
f.close()

print("Finding temperature plateau index and setting blanks there...")
def find_plateau(temps):
	segment_size = 5
	slope_thresh = 0.01
	for i in range(len(temps)):
		m,b = numpy.polyfit(range(segment_size), temps[i:i+segment_size], 1)
		#print("numpy.polyfit("+str(range(segment_size))+", "+str(temps[i:i+segment_size])+", 1)")
		#print(str(i)+": m,b = "+str(m)+", "+str(b))
		if abs(m)<slope_thresh:
			print(i)
			return i
			break
for res in range(NUM_RESISTORS):
	plateauIndex = find_plateau(temps[res])
	print("  - Resistor #"+str(res)+": "+str(plateauIndex))
	blanks[res] = data_raw[res][plateauIndex]


	
print("Converting raw data to OD...")
for res in range(NUM_RESISTORS):
	print("   - Resistor #"+str(res)+"...")
	for i in range(len(data_raw[res])):
		oddata = []
		for w in range(96):
			#print("Resistor #"+str(res)+", data_point #"+str(i)+", well #"+str(w))
			if data_raw[res][i][w] > 0:
				odval = -math.log10(float(data_raw[res][i][w]) / float(blanks[res][w]))
			else:
				odval = -1
			oddata.append(odval)
		data_od[res].append(oddata)
			

print("Done processing data. Dumping into spreadsheet...")
		
print("   Setting up worksheets...")
book = xlwt.Workbook(encoding="utf-8")

sheets_raw = []
for i in range(NUM_RESISTORS):
	sheets_raw.append(book.add_sheet("RES"+str(i)+"_raw"))
	sheets_raw[i].set_panes_frozen(True)
	sheets_raw[i].set_horz_split_pos(1)
	sheets_raw[i].set_vert_split_pos(2)
sheets_od = []
for i in range(NUM_RESISTORS):
	sheets_od.append(book.add_sheet("RES"+str(i)+"_od"))
	sheets_od[i].set_panes_frozen(True)
	sheets_od[i].set_horz_split_pos(1)
	sheets_od[i].set_vert_split_pos(2)


print("   Generating header row...")
headerrow = []
headerrow.append('UNIX Timestamp')
headerrow.append('Temperature (deg. C)')
for c in range(96):
	plateCol = c % 12 + 1
	plateRow = c // 12
	if plateRow==0:
		headerrow.append('A'+str(plateCol))
	elif plateRow==1:
		headerrow.append('B'+str(plateCol))
	elif plateRow==2:
		headerrow.append('C'+str(plateCol))
	elif plateRow==3:
		headerrow.append('D'+str(plateCol))
	elif plateRow==4:
		headerrow.append('E'+str(plateCol))
	elif plateRow==5:
		headerrow.append('F'+str(plateCol))
	elif plateRow==6:
		headerrow.append('G'+str(plateCol))
	elif plateRow==7:
		headerrow.append('H'+str(plateCol))

headerStyle = xlwt.XFStyle()
headerFont = xlwt.Font()
headerFont.bold = True
headerStyle.font = headerFont
headerBorders = xlwt.Borders()
headerBorders.bottom = xlwt.Borders.MEDIUM
headerStyle.borders = headerBorders

for res in range(NUM_RESISTORS):
	print("   Writing Resistor #"+str(res)+"'s data...")
	rows = len(data_raw[res])
	cols = 98 #timestamp, temperature, 96 wells
	if rows > 0:
		for c in range(cols):
			sheets_raw[res].write(0,c,headerrow[c], style=headerStyle)
			sheets_od[res].write(0,c,headerrow[c], style=headerStyle)
		for r in range(rows):
			for c in range(cols):
				if c==0:
					sheets_raw[res].write(r+1, c, timestamps[res][r]) #write timestamp first
					sheets_od[res].write(r+1, c, timestamps[res][r]) #write timestamp first
				elif c==1:
					sheets_raw[res].write(r+1, c, temps[res][r]) #write temperature second
					sheets_od[res].write(r+1, c, temps[res][r]) #write temperature second
				else:
					sheets_raw[res].write(r+1, c, data_raw[res][r][c-2]) #write data for everything else
					sheets_od[res].write(r+1, c, data_od[res][r][c-2]) #write data for everything else

print("Saving...")
#Generate XLS filename by separating the old extension (presumably .txt) and changing it to .xls:
filename = filepath.split('.')
filename[-1] = 'xls'
filename = '.'.join(filename)

#Save the file:
book.save(filename)

print("Done.")
