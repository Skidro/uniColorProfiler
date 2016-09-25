from generic_page import *
from collections import OrderedDict as od

class advanced_analysis(File):
	""" This is a subclass of 'File' type objects which is created
	    to carry out second level of memory page analysis """

	def __init__(self, filename):
		super(advanced_analysis, self).__init__(filename)

		# Create a hash for parsed data
		self.data_hash = {}
		self.mem_areas = {}

		# Create the name for output file
		self.out_file = self.name + '.ord'
		self.memar_fd = '../data_1/memareas.profile'

		# Call the parse method
		self.parse()

		# Call the mem-areas profile
		self.parse_memareas()

		# Print the parsed data
		self.print_data()

	def parse(self):
		""" Parse the data in the file """

		# Open and parse the file
		with open(self.name, 'r') as fdi:
			for line in fdi:
				words = [word for word in line.split(' ') if word != ' ' and word != ':']
				
				# Store the data in the hash
				self.data_hash[int(words[0], 16)] = int(words[1])

		# Sort the dictionary by addresses
		self.data_hash = od(sorted(self.data_hash.items(), key = lambda t : t[0]))

		print 'Total Bytes :', float(sum(self.data_hash.values())) / 1024 / 1024

		return

	def parse_memareas(self):
		""" Parse the file which contains memareas profile """

		# Open and parse the memareas-file
		with open(self.memar_fd) as fdi:
			for line in fdi:
				words = [word for word in line.split(' ') if word != '']

				# Extract the start and end address of the memory area
				mem_range = words[0].split('-')

				try:
					start_address = int(mem_range[0], 16)
					end_address   = int(mem_range[1], 16)
				except:
					raise ValueError, 'Unable to convert mem-range : (%s)' % (words[0])

				# Push the end address, size and designation of this area in the hash
				self.mem_areas[start_address] = (end_address, end_address - start_address, words[-1])

		# Sort the dictionary by start addresses
		self.mem_areas = od(sorted(self.mem_areas.items(), key = lambda t : t[0]))

		return

	def print_data(self):
		""" This is the function for storing the output data """

		# Open the output file
		fdo = open(self.out_file, 'w')

		for area in self.mem_areas.keys():
			fdo.write('\nArea Range : 0x%.9x - 0x%.9x\n\n' % (area, self.mem_areas[area][0]))
			for key in self.data_hash.keys():
				if key > area and key < self.mem_areas[area][0]:
					# Find out if the page lies in the memory area
					fdo.write('0x%.8x : %d\n' % (key, self.data_hash[key]))

		fdo.close()

		return

def main():
	""" This is the primary entry point into the application """

	# Parse the file
	mem_file = advanced_analysis('../data_1/mempages.dat.out')

# Designate main as the entry point into the application
if __name__ == '__main__':
	# Invoke the main function
	main()
