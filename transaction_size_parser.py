import struct
import datetime
import os
import bokeh.io
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid, Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from flask import Flask, render_template

############################################################################################################
################################################ PYTHON FUNCTIONS ##########################################
data = {"Block": [], "Transactions": []} #Dict used to hold graph data
updateData = []
numBlocksPerHundred = []

def parseBlockFile(blockfile):
	block = Block()
	block.parseBlockFile(blockfile)

def read_1bit(stream):
	return ord(stream.read(1))

def read_2bit(stream):
	return struct.unpack('H', stream.read(2))[0] #Reads 2 bytes and returns value 

def read_4bit(stream):
	return struct.unpack('I', stream.read(4))[0] #Reads 4 bytes and returns value

def read_8bit(stream):
	return struct.unpack('Q', stream.read(8))[0] #Reads 8 bytes and returns value

def reverse32(stream):
	return stream.read(32)[::-1] #Convert big endian --> little endian (32 byte)

def read_timeStamp(stream):
	utctime = read_4bit(stream) #Timestamp info
	return utctime

def read_varint(stream): #Function for variable integers e.g. transaction size
	ret = read_1bit(stream)

	if ret < 0xfd: #One byte integer
		return ret
	if ret == 0xfd: #Read next two bytes
		return read_2bit(stream)
	if ret == 0xfe: #Read next four bytes
		return read_4bit(stream)
	if ret == 0xff: #Read next eight bytes
		return read_8bit(stream)
	return -1

def get_hexstring(bytebuffer): #Function for returning hashes
	return(''.join(('%x' %i for i in bytebuffer)))

############################################################################################################
################################################ BOOKEH FUNCTIONS ##########################################

def create_hover_tool(): #Hover tool for barchart
	hover_html = """
		<div>
			<span class = "hover_tooltip">Block Range: $x</span>
		</div>
		<div>
			<span class = "hover_tooltip">@Transactions transaction(s)</span>
		</div>
	"""
	return HoverTool(tooltips = hover_html)

def create_bar_chart(data, title, x_name, y_name, hover_tool = None, width = 1200, height = 300): #Function for creating barchart
	source = ColumnDataSource(data)
	xdr = FactorRange(factors = data[x_name])
	ydr = Range1d(start = 0, end = max(data[y_name])*1.3)

	tools = []
	if hover_tool:
		tools = [hover_tool,]

	plot = figure(title=title, x_range=xdr, y_range=ydr, plot_width=width,
                  plot_height=height, h_symmetry=False, v_symmetry=False,
                  min_border=0, toolbar_location="above", tools=tools,
                  responsive=True, outline_line_color="#666666")

	glyph = VBar(x = x_name, top = y_name, bottom = 0, width = 0.8, fill_color = "#e12127")
	plot.add_glyph(source, glyph)

	xaxis = LinearAxis()
	yaxis = LinearAxis()

	plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
	plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
	plot.toolbar.logo = None
	plot.min_border_top = 0
	plot.xgrid.grid_line_color = None
	plot.ygrid.grid_line_color = "#999999"
	plot.yaxis.axis_label = "Number of Transactions"
	plot.ygrid.grid_line_alpha = 0.1
	plot.xaxis.axis_label = "Block Number"
	plot.xaxis.major_label_orientation = 1
	return plot

app = Flask(__name__)

@app.route("/<int:blocks_count>/")

def chart(blocks_count):
	if blocks_count <= 0:
		blocks_count = 1

	for i in range(1, blocks_count):
		data["Block"].append(i)
		data["Transactions"].append(i)

	hover = create_hover_tool()
	plot = create_bar_chart(data, "Number of transactions per 50 blocks", "Block", "Transactions", hover)

	script, div = components(plot)

	return render_template("chart.html", blocks_count = blocks_count, the_div = div, the_script = script)

############################################################################################################
############################################### BLOCK READER ###############################################

class Block(object):

	def __init__(self):
		self.magic_no = -1
		self.blocksize = 0
		self.blockheader = None
		transaction_count = 0
		transactions = None
		blockfile = None

	def parseBlockFile(self, blockfile): #Block parsing function for 140,000 blocks

		blockNumber = 0
		with open(blockfile, 'rb') as bf: #Parses first blockfile
			countBytes = 0
			blockFileSize = os.path.getsize(blockfile)

			for i in range(0, blockFileSize, 223):
				if countBytes == 0:	
					data["Block"].append(blockNumber)
					self.magic_no = read_4bit(bf)
					self.blocksize = read_4bit(bf)
					countBytes += self.blocksize + 8
					self.blockheader = BlockHeader()
					self.blockheader.parse(bf)
					self.transaction_count = read_varint(bf)
					data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				elif countBytes < blockFileSize:
					with open(blockfile, 'rb') as newbf:
						data["Block"].append(blockNumber)
						newbf.seek(countBytes)
						self.magic_no = read_4bit(newbf)
						self.blocksize = read_4bit(newbf)
						countBytes += self.blocksize + 8
						self.blockheader = BlockHeader()
						self.blockheader.parse(newbf)
						self.transaction_count = read_varint(newbf)
						data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				else:
					bf.close()

				blockNumber += 1

		with open("blk00001.dat", 'rb') as bf: #Parses second file
			countBytes = 0
			blockFileSize = os.path.getsize("blk00001.dat")

			for i in range(0, blockFileSize, 223):
				if countBytes == 0:	
					data["Block"].append(blockNumber)
					self.magic_no = read_4bit(bf)
					self.blocksize = read_4bit(bf)
					countBytes += self.blocksize + 8
					self.blockheader = BlockHeader()
					self.blockheader.parse(bf)
					self.transaction_count = read_varint(bf)
					data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				elif countBytes < blockFileSize:
					with open("blk00001.dat", 'rb') as newbf:
						data["Block"].append(blockNumber)
						newbf.seek(countBytes)
						self.magic_no = read_4bit(newbf)
						self.blocksize = read_4bit(newbf)
						countBytes += self.blocksize + 8
						self.blockheader = BlockHeader()
						self.blockheader.parse(newbf)
						self.transaction_count = read_varint(newbf)
						data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				else:
					bf.close()

				blockNumber += 1

		with open("blk00002.dat", 'rb') as bf: #Parses third blockfile
			countBytes = 0
			blockFileSize = os.path.getsize("blk00002.dat")

			for i in range(0, blockFileSize, 223):
				if countBytes == 0:	
					data["Block"].append(blockNumber)
					self.magic_no = read_4bit(bf)
					self.blocksize = read_4bit(bf)
					countBytes += self.blocksize + 8
					self.blockheader = BlockHeader()
					self.blockheader.parse(bf)
					self.transaction_count = read_varint(bf)
					data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				elif countBytes < blockFileSize:
					with open("blk00002.dat", 'rb') as newbf:
						data["Block"].append(blockNumber)
						newbf.seek(countBytes)
						self.magic_no = read_4bit(newbf)
						self.blocksize = read_4bit(newbf)
						countBytes += self.blocksize + 8
						self.blockheader = BlockHeader()
						self.blockheader.parse(newbf)
						self.transaction_count = read_varint(newbf)
						data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output
				else:
					bf.close()

				blockNumber += 1

		with open("blk00003.dat", 'rb') as bf: #Parses fourth blockfile
			countBytes = 0
			blockFileSize = os.path.getsize("blk00003.dat")

			for i in range(0, blockFileSize, 223):
				if countBytes == 0:	
					data["Block"].append(blockNumber)
					self.magic_no = read_4bit(bf)
					self.blocksize = read_4bit(bf)
					countBytes += self.blocksize + 8
					self.blockheader = BlockHeader()
					self.blockheader.parse(bf)
					self.transaction_count = read_varint(bf)
					data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				elif countBytes < blockFileSize:
					with open("blk00003.dat", 'rb') as newbf:
						data["Block"].append(blockNumber)
						newbf.seek(countBytes)
						self.magic_no = read_4bit(newbf)
						self.blocksize = read_4bit(newbf)
						countBytes += self.blocksize + 8
						self.blockheader = BlockHeader()
						self.blockheader.parse(newbf)
						self.transaction_count = read_varint(newbf)
						data["Transactions"].append(self.transaction_count) #Adds data to dict for graphical output

				else:
					bf.close()

				blockNumber += 1

		#Block below is how the data for this specific graph is created and added to the Dict

		numTransactionsPerHundred = []

		for i in (data["Transactions"]):
			numTransactionsPerHundred.append(i)

		j = 0
		k = 1000
		theCount = 1
		for i in range(0, len(numTransactionsPerHundred), 1000): #Does this for blocksize of 1000
			value1 = sum((numTransactionsPerHundred)[j:k])
			updateData.append(value1)
			numBlocksPerHundred.append(theCount)
			j = k
			k += 1000
			theCount += 1

		data["Block"] = numBlocksPerHundred #Updates Dict
		data["Transactions"] = updateData #Updates Dict
			
############################################################################################################
############################################### BLOCK HEADER ###############################################

class BlockHeader(object): #Represents header of the block
	
	def __init__(self):
		super(BlockHeader, self).__init__()
		self.version = None
		self.previousHash = None
		self.merkleHash = None
		self.time = None
		self.bits = None
		self.nonce = None

	def parse(self, stream):
		self.version = read_4bit(stream)
		self.previousHash = reverse32(stream)
		self.merkleHash = reverse32(stream)
		self.time = read_timeStamp(stream)
		self.bits = read_4bit(stream)
		self.nonce = read_4bit(stream)

	def __str__(self): #Function returns information of header once parsed
		return "\nVersion: %d \nPreviousHash: %s \nMerkle: %s \nTime: %s \nBits: %8x \nNonce: %8x" \
		% (self.version, get_hexstring(self.previousHash), get_hexstring(self.merkleHash), str(self.time), self.bits, self.nonce)

	def __repr__(self):
		return __str__(self)

############################################################################################################

if __name__ == "__main__":

	import sys
	usage = "Usage: pyhton {0} "
	if len(sys.argv) < 1:
		print(usage.format(sys.argv[0]))
	else: 
		parseBlockFile("blk00000.dat") #Initial file to be parsed
	app.run(debug = True)