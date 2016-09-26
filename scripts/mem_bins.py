import re
import numpy as np
import pylab as pl
import scipy.stats as stats

from generic_page import *
from helper_functions import *

# Set to 1 if debugging required
debug = 0

# Global Data
plot_data = {}
ALLD_COLORS = 0x00FFFFFF
min_file = '262'
min_rate = 3.99
min_time = 1.17
max_file = '536'
max_rate = 17.44
max_time = 1.8

class mem_color(File, Helper):
	""" A subclass of file-type objects to process miss-rate in tegra
	    platform """

	def __init__(self, filename):
		# Invoke the super-class constructor method
		super(mem_color, self).__init__(filename)

		# Parse the file
		self.parse()

		return

	def parse(self):
		""" This is the primary function for extracting color distribution information
		    from pagetype data """

		# Get a bit-list of allowed color bins
		bit_list = self.bit_numbers(ALLD_COLORS)

		total_pages = alld_clr_pages = rest_clr_pages = 0
		pages = []
		alld_pages = []

		# Open and parse the file
		with open(self.name, 'r') as fdi:
			for line in fdi:
				# Get the required lines
				total_pages_line = re.match("^.*###\D*(\d+)", line)
				color_line = re.match("^.*Color.*:\D*(\d+)", line)

				if total_pages_line:
					total_pages = int(total_pages_line.group(1))

				if color_line:
					pages.append(int(color_line.group(1)))


		if total_pages == 0 or pages == []:
			print 'Unexpected File : %s' % (self.name)

		# Extract the file number
		file_number = (re.match("^.*colors(\d+)", self.name)).group(1)

		color = 0
		for page_items in pages:
			if color in bit_list:
				alld_clr_pages += pages[color]
				alld_pages.append(pages[color])
			else:
				rest_clr_pages += pages[color]

			color += 1

		# Sort the pages in allowed colors
		sorted_clr_pages = sorted(alld_pages)

		# Calculate the standard deviation of allowed color pages
		std_clr_pages = np.std(sorted_clr_pages)
		

		# Insert the data in the hash
		plot_data[file_number] = (total_pages, alld_clr_pages, rest_clr_pages, std_clr_pages, alld_pages)

		if debug:
			print 'plot_data[' + file_number + '] : ', plot_data[file_number]
			print 'pages        : ', pages
			print 'alld_pages   : ', alld_pages
			print 'bit_list     : ', bit_list

		return

# plot_data
# Function to plot_data parsed from the files
def plotdata(position, title):
	""" Function for plotting the collected data about page distribution """

	# Font size for plot titles
	pl_fontsize = 15
	pl_rows = 1
	pl_cols = 1
	top = 35
	right = 24

	pl.bar(range(24), plot_data[max_file][-1], 1, color = 'g')

	pl.xlim(0, right)
	pl.ylim(0, top)

	pl.xlabel('Cache Colors', fontsize = pl_fontsize)
	pl.ylabel('Page Count', fontsize = pl_fontsize)

	pl.text(0.5, top - 2, 'Miss-Rate = ' + '%.2f' % max_rate + '%')
	pl.text(0.5, top - 4, 'Time = ' + '%.2f' % max_time + ' sec')
	pl.text(0.5, top - 6, r'$\sigma$ = ' + '%.2f' % plot_data[max_file][-2])

	pl.show()

	return

def do_set(platform, corun, mint, part, util, pos):
	""" Helper function for plotting mutiple data sets """

	# Reset the global plot-data hash
	plot_data = {}

	# Set the parent directory path based on platform name
	parent_dir = ''

	if platform == 'tegra':
		parent_dir = '../data/tegra/data/'
	else:
		parent_dir = '../data/'

	# Parse the data in each file
	for item in range(1, 1000):
		mem_color(parent_dir + part + '/' + corun + '/data_' + mint + '_' + part + '/' + util + '/colors' + str(item))

	# Perform the actual plotting
	title = util + '%'
	plotdata(pos, title)

	return

def main():
	""" This is the primary entry point into the script """

	# Create a figure to save all plots
	fig = pl.figure(1, figsize = (15, 5))

	# Set the partition type
	part = 'sets'
	platform = 'tegra'

	if platform == 'tegra' or part == 'ways':
		part_size = '1536'
		utilization = [100]
	else:
		part_size = '1920'
		ws_size = '1700'

	# Define the name to save the figure with
	if platform == 'tegra':
		pos = 1
		figname = 'Tegra_BW_Mint_CLRS_100_Bins_Max_Std.png'

		# Place a title for this graph
		pl.title('Distribution of Pages across Cache Colors - 100% Utilizaiton')
		
		for util in utilization:
			util = str(util)

			# Plot the data one set at a time
			do_set(platform, 'solo', 'mint', part, util, pos)

			# Update the position for the next plot
			pos += 1		
	else:
		figname = 'Xeon_BW_' + part.upper() + '_CLRS.png'

		# Place a title for this graph
		pl.suptitle('Xeon | BW-R | ' + part_size + ' | ' + ws_size + ' | ' + part[0].upper() + part[1:] + ' | Colors');

		# Plot the data one set at a time
		do_set(platform, 'solo', 'mint', '', part, 1)
		do_set(platform, 'corun', 'mint', '', part, 3)
		do_set(platform, 'solo', 'modf', '', part, 2)
		do_set(platform, 'corun', 'modf', '', part, 4)		

	fig.savefig(figname)
	
	return

# Desginate main as the entry point
if __name__ == "__main__":
	# Call the main function
	main()
