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
avg_std = []
extrema_std = []
extrema_files = []
ALLD_COLORS = 0x00FFFFFF

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
		plot_data[file_number] = (total_pages, alld_clr_pages, rest_clr_pages, std_clr_pages)

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

	std_clr_array = []
	alld_pages_array = []
	rest_pages_array = []
	total_pages_array = []
	number = 0
	max_std = 0.0
	min_std = 100.0
	for item in plot_data.keys():
		std_clr_array.append(plot_data[item][3])
		rest_pages_array.append(plot_data[item][2])
		alld_pages_array.append(plot_data[item][1])
		total_pages_array.append(plot_data[item][0])

		if std_clr_array[number] > max_std:
			max_std = std_clr_array[number]
			max_file = int(item)

		if std_clr_array[number] < min_std:
			min_std = std_clr_array[number]
			min_file = int(item)
			
		number += 1
	
	net_pages = sum(total_pages_array)
	net_alld_pages = sum(alld_pages_array)
	net_rest_pages = sum(rest_pages_array)

	# Sort the data
	std_array = sorted(std_clr_array)

	if debug:
		# Display the data
		print "Max File : %d | Min File : %d" % (max_file, min_file)
		print "Max Std : %.3f | Min Std : %.3f " % (max_std, min_std)

	# Calculate the mean and standard deviation
	std_clr_mean = np.mean(std_array)
	std_clr_std  = np.std(std_array)
	
	# Push the data into the global arrays
	avg_std.append(std_clr_mean)
	extrema_std.append((min_std, max_std))
	extrema_files.append((min_file, max_file))

	# Fit a normal curve on the sorted data
	fit = stats.norm.pdf(std_array, std_clr_mean, std_clr_std)

	# Create a sub-plot for all the plots
	pl.subplot(pl_rows, pl_cols, position)

	# Plot the normal curve
	pl.plot(std_array, fit)

	# Plot the histogram along the curve
	pl.hist(std_array, normed = True, bins = np.arange(min_std, max_std, ((max_std - min_std) / 10)))

	# Plot vertical lines to indicate min-max values
	pl.plot([max_std, max_std], [0, 1], '-r')
	pl.plot([min_std, min_std], [0, 1], '-g')

	# State the x-label and y-label
	pl.xlabel(r'$\sigma$ of Page Distribution')
	pl.ylabel('PDF')

	# Set axes limits
	pl.xlim(0, 8)
	pl.ylim(0, 1)

	# Set the title of the plot
	pl.text(std_clr_mean + 0.2, 0.9, r'$\mu$ = ' + format(std_clr_mean, '0.2f'))
	pl.text(max_std + 0.1, 0.5, r'max( $\sigma$ ) = ' + format(max_std, '0.2f'))
	pl.text(min_std - 1.75, 0.5, r'min( $\sigma$ ) = ' + format(min_std, '0.2f'))

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
	fig = pl.figure(1, figsize = (10, 8))

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
		figname = 'Tegra_BW_Mint_CLRS_Scaled.png'

		# Place a title for this graph
		pl.title('BW-R Solo PDF of Page Distribution - 100% Utilizaiton')
		
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
	
	# Print the global data
	print '<Std>      : ', avg_std
	print '[Std]      : ', extrema_std
	print 'Files      : ', extrema_files
	
	return

# Desginate main as the entry point
if __name__ == "__main__":
	# Call the main function
	main()
