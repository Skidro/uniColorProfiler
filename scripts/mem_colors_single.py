import re, sys
import numpy as np
import pylab as pl
import scipy.stats as stats
from math import ceil

from generic_page import *
from helper_functions import *

# Set to 1 if debugging required
pdf_std_debug = 0

# Global Data
plot_std_clr_data = {}
ALLD_COLORS = 0x0FFFFFFF

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
			sys.exit(2)

		# Extract the file number
		file_number = (re.match("^.*/(\d+)$", self.name)).group(1)

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
		plot_std_clr_data[file_number] = (total_pages, alld_clr_pages, rest_clr_pages, std_clr_pages)

		return

# plot_clr_pdf
# Function to plot probability density function of color distribution of pages
def plot_clr_pdf(title):
	""" Function for plotting the collected data about page distribution """

	# Font size for plot titles
	pl_fontsize = 15
	pl_rows = 1
	pl_cols = 1

	pdf_clr_std_data = {}
	std_clr_array = []
	alld_pages_array = []
	rest_pages_array = []
	total_pages_array = []
	number = 0
	max_std = 0.0
	min_std = 100.0

	for item in plot_std_clr_data.keys():
		std_clr_array.append(plot_std_clr_data[item][3])
		rest_pages_array.append(plot_std_clr_data[item][2])
		alld_pages_array.append(plot_std_clr_data[item][1])
		total_pages_array.append(plot_std_clr_data[item][0])

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

	# Calculate the mean and standard deviation
	std_clr_mean = np.mean(std_array)
	std_clr_std  = np.std(std_array)
	
	# Push the data into the global arrays
	pdf_clr_std_data['average'] = std_clr_mean
	pdf_clr_std_data['extrema_std'] = (min_std, max_std)
	pdf_clr_std_data['extrema_files'] = (min_file, max_file)

	# Fit a normal curve on the sorted data
	fit = stats.norm.pdf(std_array, std_clr_mean, std_clr_std)

	# Plot the normal curve
	pl.plot(std_array, fit)

	# Plot the histogram along the curve
	hist_bins = np.arange(min_std, max_std, ((max_std - min_std) / 10))
	hist_x, hist_y, _ = pl.hist(std_array, normed = True, bins = hist_bins)
	y_limit = ceil(hist_x.max()) + 0.1

	# Plot vertical lines to indicate min-max values
	pl.plot([max_std, max_std], [0, y_limit], '-r')
	pl.plot([min_std, min_std], [0, y_limit], '-g')

	# State the x-label and y-label
	pl.xlabel(r'$\sigma$ of Page Distribution')
	pl.ylabel('PDF')

	# Hide the ticks on the y-axis
	pl.gca().yaxis.set_major_locator(pl.NullLocator())

	# Set axes limits
	pl.xlim(0, 12)
	pl.ylim(0, y_limit)

	# Set the title of the plot
	if ((max_std - min_std) < 2):
		pl.text(max_std + 0.1, y_limit - 5, r'$\mu$ = ' + format(std_clr_mean, '0.2f'))
	else:
		pl.text(std_clr_mean + 0.2, y_limit - 0.4, r'$\mu$ = ' + format(std_clr_mean, '0.2f'))

	pl.text(max_std + 0.1, 5, r'max( $\sigma$ ) = ' + format(max_std, '0.2f'), color = 'r')

	if (min_std < 2):
		pl.text(max_std + 0.1, 2, r'min( $\sigma$ ) = ' + format(min_std, '0.2f'), color = 'g')
	else:
		pl.text(min_std - 1.75, 0.5, r'min( $\sigma$ ) = ' + format(min_std, '0.2f'), color = 'g')
		
	pl.title(title)

	if pdf_std_debug:
		pl.show()

	return pdf_clr_std_data

def do_clr_pdf(parent_dir, print_title):
	""" Helper function for making a single plot """

	# Create dimensions for the plot
	fig = pl.figure(1, figsize = (10, 8))
	figname = ('_'.join(parent_dir.split('/')[2:]))[:-1] + '.png'

	# Parse the data in each file
	for item in range(1, 251):
		mem_color(parent_dir + str(item))

	# Perform the actual plotting
	util  = str(re.match(r'^.*/(\d+)/$', parent_dir).group(1))
	corun = str(re.match(r'^.*/(\d+)/.*/$', parent_dir).group(1))
	
	if print_title:
		title = 'Corun : %s | Utilization : %s%%' % (corun, util)
	else:
		title = ''

	pdf_clr_hash = plot_clr_pdf(title)

	# Save the figure
	fig.savefig('../figs/' + figname)

	return pdf_clr_hash

def main():

	# Plot the data set
	do_clr_pdf('../data/TG/BW/UN/PL/CL/00/100/', True)

	return

# Desginate main as the entry point
if __name__ == "__main__":
	# Call the main function
	main()
