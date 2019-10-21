import struct
import datetime
import os
import random
import bokeh.io
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid, Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from flask import Flask, render_template

############################################################################################################
################################################ FUNCTIONS #################################################
data = { "Block": [], "Transactions": []} #Dict used to hold graph data

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
	return stream.read(32)[::-1] #Convert big endian --> little endian

def read_timeStamp(stream): #Timestamp info
	utctime = read_4bit(stream)
	return utctime

def read_varint(stream):
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

def get_hexstring(bytebuffer):
	return(''.join(('%x' %i for i in bytebuffer)))

############################################################################################################
################################################ BOOKEH FUNCTIONS ##########################################

def create_hover_tool(): #Hover tool for barchart
	hover_html = """
		<div>
			<span class = "hover_tooltip">$x BTC</span>
		</div>
		<div>
			<span class = "hover_tooltip">i = Transaction Value</span>
		</div>
		<div>
			<span class = "hover_tooltip">@Transactions transactions belong in this range</span>
		</div>
	"""
	return HoverTool(tooltips = hover_html)

def create_bar_chart(data, title, x_name, y_name, hover_tool = None, width = 1200, height = 300):
	source = ColumnDataSource(data)
	xdr = FactorRange("0 < i < 0.01", "0.01 <= i < 0.1", "0.1 <= i < 1", "1 <= i < 5", "5 <= i < 25", "25 <= i < 50", "50 <= i < 250", "250 <= i < 1000", "i => 1000")
	ydr = Range1d(start = 0, end = max(data[y_name])*1.1)

	tools = []
	if hover_tool:
		tools = [hover_tool]

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
	plot.yaxis.axis_label = "Number of transactions"
	plot.ygrid.grid_line_alpha = 0.1
	plot.xaxis.axis_label = "Amount of BTC transacted (i = transaction value)"
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
	plot = create_bar_chart(data, "Ranges of the value of transactions (BTC)", "Block", "Transactions", hover)

	script, div = components(plot)

	return render_template("chart_04.html", blocks_count = blocks_count, the_div = div, the_script = script)

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

	def parseBlockFile(self, blockfile):
		print("Parsing block")

		#Creates variables for transaction ranges
		btcRangeLesser = 0
		btcRangeLess = 0
		btcRange1 = 0
		btcRange5 = 0
		btcRange25 = 0
		btcRange50 = 0
		btcRange250 = 0
		btcRange1000 = 0
		btcRangePlus = 0

		with open('transactions0.txt', 'r') as t: #Opens and read stored transaction information
			transactionVals = [line.strip() for line in t] #Stores read data into list
		
		#For loop to assign a range for each value	
		for i in transactionVals:
			transactionValue = float(i)/100000000.00
			if transactionValue < 0.01:
				btcRangeLesser += 1
			elif 0.01 <= transactionValue < 0.1:
				btcRangeLess += 1
			elif 0.1 <= transactionValue < 1:
				btcRange1 += 1
			elif 1 <= transactionValue < 5:
				btcRange5 += 1
			elif 5 <= transactionValue < 25:
				btcRange25 += 1
			elif 25 <= transactionValue < 50:
				btcRange50 += 1
			elif 50 <= transactionValue < 250:
				btcRange250 += 1
			elif 250 <= transactionValue < 1000:
				btcRange1000 += 1
			else:
				btcRangePlus += 1

		data["Transactions"].append(btcRangeLesser)
		data["Transactions"].append(btcRangeLess)
		data["Transactions"].append(btcRange1)
		data["Transactions"].append(btcRange5)
		data["Transactions"].append(btcRange25)
		data["Transactions"].append(btcRange50)
		data["Transactions"].append(btcRange250)
		data["Transactions"].append(btcRange1000)
		data["Transactions"].append(btcRangePlus)

		numTransactions = len(transactionVals)

		blockNum = 1
		while blockNum <= len(data["Transactions"]):
			data["Block"].append(blockNum)
			blockNum += 1
			
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
############################################### TRANSACTIONS ###############################################
class tx_Input(object): #Class for retreiving transaction input information

	def __init__(self):
		super(tx_Input, self).__init__()

	def parse(self, stream):
		self.previousHash = reverse32(stream)
		self.prevTx_out_idx = read_4bit(stream)
		self.txIn_script_len = read_varint(stream)
		self.scriptSig = stream.read(self.txIn_script_len)
		self.seqNo = read_4bit(stream)

	def __str__(self):
		return "\nPrevious Hash: %s \nTransaction out index: %s \nTransaction in script lengh: %s \nscriptSig: %s \nSequence Number: %8x" \
		% (get_hexstring(self.previousHash), self.prevTx_out_idx, self.txIn_script_len, get_hexstring(self.scriptSig), self.seqNo)

	def __repr__(self):
		return __str__(self)


class tx_Output(object): #Class for retreiving transaction output information

	def __init__(self):
		super(tx_Output, self).__init__()

	def parse(self, stream):
		self.value = read_8bit(stream)
		self.txOut_script_len = read_varint(stream)
		self.scriptPubKey = stream.read(self.txOut_script_len)

	def __str__(self):
		return "Value (Satoshis): %d (%f btc)\nTransaction out script lengh: %d\nScript PubKey: %s" \
		% (self.value, (1.0*self.value)/100000000.00, self.txOut_script_len, get_hexstring(self.scriptPubKey))

	def __repr__(self):
		return __str__(self)

class transactions(object): #Class for retreiving all transaction information

	def __init__(self):
		super(transactions, self).__init__()
		self.version = None
		self.in_count = None
		self.inputs = None
		self.out_count = None
		self.outputs = None
		self.lock_time = None

	def parse(self, stream):
		self.version = read_4bit(stream)
		self.in_count = read_varint(stream)
		self.inputs = []

		if self.in_count > 0:
			for i in range(0, self.in_count):
				input = tx_Input()
				input.parse(stream)
				self.inputs.append(input)

		self.out_count = read_varint(stream)
		self.outputs = []

		if self.out_count > 0:
			for i in range(0, self.out_count):
				output = tx_Output()
				output.parse(stream)
				self.outputs.append(output)

		self.lock_time = read_4bit(stream)

	def __str__(self):
		s = "Inputs count: %d\n---Inputs---\n%s\nOutputs count: %d\n---Outputs---\n%s\nLock time: %8x" \
		% (self.in_count, '\n'.join(str(i) for i in self.inputs), self.out_count, '\n'.join(str(o) for o in self.outputs), self.lock_time)

		return s

############################################################################################################
if __name__ == "__main__":

	import sys
	usage = "Usage: pyhton {0} "
	if len(sys.argv) < 1:
		print(usage.format(sys.argv[0]))
	else: 
		parseBlockFile("blk00000.dat") #Initial file to be parsed
	app.run(debug = True)