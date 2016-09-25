import re
import numpy as np
import pylab as pl
import scipy.stats as stats

from generic_page import *

# Set to 1 for debugging
debug = 0

# Global Data
plot_data = {}
avg_miss_rate = []
avg_time = []
extrema_miss_rate = []
extrema_time = []
extrema_files = []

class mem_page(File):
	""" A subclass of file-type objects to process miss-rate in tegra
	    platform """

	def __init__(self, filename, platform = 'Xeon'):
		# Invoke the super-class constructor method
		super(mem_page, self).__init__(filename)

		# Declare the platform type for this file object
		self.platform = platform

		# Parse the file
		self.parse()

		return

	def parse(self):
		""" This is the primary function for extracting miss-rate from a perf log file """
		accesses = misses = time = 0

		# Open and parse the file
		with open(self.name, 'r') as fdi:
			for line in fdi:
				# Check the platform type to select appropriate regex
				if self.platform == 'Xeon':
					# Get the required lines
					refsLine = re.match('^\D*([\d,]+) cache-references.*$', line)
					missLine = re.match('^\D*([\d,]+) cache-misses.*$', line)
					timeLine = re.match('^\D*([\d.]+) seconds time.*$', line)
				else:
					# Get the required lines
					refsLine = re.match('^\D*([\d,]+) r50.*$', line)
					missLine = re.match('^\D*([\d,]+) r52.*$', line)
					timeLine = re.match('^\D*([\d.]+) seconds time.*$', line)

				if refsLine:
					accesses = int(re.sub('\D', '', refsLine.group(1)))

				if missLine:
					misses   = int(re.sub('\D', '', missLine.group(1)))

				if timeLine:
					try:
						time = float(timeLine.group(1))
					except:
						raise ValueError, 'Could not convert string (%s) to float' % (time.group(1))

		if accesses == 0 or misses == 0 or time == 0:
			print 'Unexpected File : %s' % (self.name)

		# Extract the file number
		file_number = (re.match("^.*log(\d+)", self.name)).group(1)

		# Insert the data in the hash
		plot_data[file_number] = (accesses, misses, time)

		return

# plot_data
# Function to plot_data parsed from the files
def plotdata(position, title):
	""" Function for plotting the collected data about miss-rate """

	# Font size for plot titles
	pl_fontsize = 10
	pl_rows = 2
	pl_cols = 7

	mr_array_usort = []
	time_array = []
	number = 0
	max_rate = 0.0
	min_rate = 100.0
	for item in plot_data.keys():
		mr_array_usort.append((float(plot_data[item][1])/plot_data[item][0]) * 100)
		time_array.append(plot_data[item][2])

		if mr_array_usort[number] > max_rate:
			max_rate = mr_array_usort[number]
			max_file = int(item)

		if mr_array_usort[number] < min_rate:
			min_rate = mr_array_usort[number]
			min_file = int(item)
			
		number += 1

	# Sort the data
	mr_array = sorted(mr_array_usort)
	time_array = sorted(time_array)

	if debug:
		print "Max File : %d | Min File : %d" % (max_file, min_file)
		print "Max Time : %.3f | Max Accesses : %10d | Max Misses : %10d | Max Miss-Rate : %.3f %%" % (float(plot_data[str(max_file)][2]), int(plot_data[str(max_file)][0]), int(plot_data[str(max_file)][1]), float(mr_array[-1]))
		print "Min Time : %.3f | Min Accesses : %10d | Min Misses : %10d | Min Miss-Rate : %.3f %%" % (float(plot_data[str(min_file)][2]), int(plot_data[str(min_file)][0]), int(plot_data[str(min_file)][1]), float(mr_array[0]))

		# Parse the max file and min file
		fdmx = mem_page(fileDir + filePre + str(max_file))
		fdmn = mem_page(fileDir + filePre + str(min_file))
		max_pages, max_pages_std = fdmx.parse_file()
		min_pages, min_pages_std = fdmn.parse_file()

		print "Max Pages - %d -> %.3f MB" % (max_pages, float(max_pages * 4) / 1024)
		print "Min Pages - %d -> %.3f MB" % (min_pages, float(min_pages * 4) / 1024)

	# Calculate the mean and standard deviation
	mr_mean = np.mean(mr_array)
	mr_std  = np.std(mr_array)
	tm_mean = np.mean(time_array)
	tm_std  = np.std(time_array)
	tm_min  = time_array[0]
	tm_max  = time_array[-1]

	# Push the data regarding the plots in the global arrays
	avg_miss_rate.append(mr_mean)
	avg_time.append(tm_mean)
	extrema_files.append((min_file, max_file))
	extrema_miss_rate.append((min_rate, max_rate))
	extrema_time.append((tm_min, tm_max))

	# Fit a normal curve on the sorted data
	fit = stats.norm.pdf(mr_array, mr_mean, mr_std)

	# Create a sub-plot for all the plots
	pl.subplot(pl_rows, pl_cols, position)

	# Plot the normal curve
	pl.plot(mr_array, fit)

	# Plot the histogram along the curve
	pl.hist(mr_array, normed = True, bins = np.arange(min_rate, max_rate, (max_rate - min_rate)/10))

	# Plot vertical lines to indicate min-max values
	pl.plot([max_rate, max_rate], [0, 1], '-r')
	pl.plot([min_rate, min_rate], [0, 1], '-g')

	# State the x-label and y-label
	pl.xlabel('Miss-Rate')
	pl.ylabel('PDF')

	# Create a title for this plot
	pl.title('< ' + format(mr_mean, '0.2f') + '% > | [ ' + format(max_rate, '0.2f') + '% ] | ( ' + format(min_rate, '0.2f') + '% ) | ' + title, fontsize = pl_fontsize)

	# Set axes limits
	pl.xlim(0, 50)
	# pl.ylim(0, 1)

	# Create a subplot for timing bars
	mrate_pl = pl.subplot(pl_rows, pl_cols, position + pl_cols)

	# Fit a normal curve on sorted timing data
	fit = stats.norm.pdf(time_array, tm_mean, tm_std)

	# Plot the normal curve
	pl.plot(time_array, fit) 

	# Plot data histograms along the curve
	pl.hist(time_array, normed = True, bins = np.arange(tm_min, tm_max, (tm_max - tm_min)/10))

	# Plot vertical lines to indicate min-max values
	pl.plot([tm_max, tm_max], [0, 7], '-r')
	pl.plot([tm_min, tm_min], [0, 7], '-g')

	# Label the axis
	pl.xlabel('Time (seconds)')
	pl.ylabel('PDF')

	# Create a title for the plot
	pl.title('< ' + format(tm_mean, '0.3f') + ' sec > | [ ' + format(tm_max, '0.3f') + ' ] | ( ' + format(tm_min, '0.3f') + ' sec )', fontsize = pl_fontsize)

	# Set axes limits
	pl.xlim(0, 2)
	# pl.ylim(0, 1)

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
		mem_page(parent_dir + part + '/' + corun + '/data_' + mint + '_' + part + '/' + util + '/log' + str(item), platform)

	# Perform the actual plotting
	title = util + '%'
	plotdata(pos, title)

	return

def main():
	""" This is the primary entry point into the script """

	# Create a figure to save all plots
	fig = pl.figure(1, figsize = (35, 15))

	# Set the partition type
	part = 'sets'
	platform = 'tegra'

	if platform == 'tegra' or part == 'ways':
		part_size = '1536'
		utilization = [25, 37, 50, 63, 75, 87, 100]
	else:
		part_size = '1920'
		ws_size = '1700'

	# Define the name to save the figure with
	if platform == 'tegra':
		pos = 1
		figname = 'Tegra_BW_Mint_Col.png'

		# Place a title for these plots
		pl.suptitle('Tegra | BW-R | ' + part_size + ' | Solo | Mint | Sets')

		for util in utilization:
			util = str(util)

			# Plot the data one set at a time
			do_set(platform, 'solo', 'mint', part, util, pos)

			# Update the position for the next plot
			pos += 1
	else:
		figname = 'Xeon_BW_' + part.upper() + '.png'

		# Place a title for these plots
		pl.suptitle('Xeon | BW-R | ' + part_size + ' | ' + ws_size + ' | ' + part[0].upper() + part[1:])

		# Plot the data one set at a time
		do_set(platform, 'solo', 'mint', '', part, 1)
		do_set(platform, 'corun', 'mint', '', part, 3)
		do_set(platform, 'solo', 'modf', '', part, 2)
		do_set(platform, 'corun', 'modf', '', part, 4)

	# Save the figure
	fig.savefig(figname)

	# Print the global data
	print '<Time>      : ', avg_time
	print '<Miss Rate> : ', avg_miss_rate
	print '[Time]      : ', extrema_time
	print '[Miss-Rate] : ', extrema_miss_rate
	print 'Files       : ', extrema_files

	return

# Desginate main as the entry point
if __name__ == "__main__":
	# Call the main function
	main()
