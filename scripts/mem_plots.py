import re
import numpy as np
import pylab as pl

from generic_page import File

# Set to 1 for debugging
debug = 0

# Global Data
plot_data = {}
parsed_miss_data = []
parsed_time_data = []

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

	mr_array_usort = []
	time_array = []

	for item in plot_data.keys():
		mr_array_usort.append((float(plot_data[item][1])/plot_data[item][0]) * 100)
		time_array.append(plot_data[item][2])

	# Push the miss-rate data into global array
	parsed_miss_data.append(mr_array_usort)
	parsed_time_data.append(time_array)

	return
	
	
def do_set(platform, corun, mint, part, util, pos):
	""" Helper function for plotting mutiple data sets """

	# Set the parent directory path based on platform name
	parent_dir = ''

	if platform == 'tegra':
		parent_dir = '../data/tegra/data/'
	else:
		parent_dir = '../data/'

	# Parse the data in each file
	for item in range(1, 1000):
		mem_page(parent_dir + part + '/' + corun + '/3/data_' + mint + '_' + part + '/' + util + '/log' + str(item), platform)

	# Perform the actual plotting
	title = util + '%'
	plotdata(pos, title)

	return

def do_box_plot(figname, utilization, parsed_miss_data):
	""" This function can be used for drawing box plots """

	# Set uniform fontsize for all the captions
	pl_fontsize = 15

	# Create a figure to save all plots
	fig, ax1 = pl.subplots(figsize = (10, 8))

	bp = pl.boxplot(parsed_miss_data, notch=0, sym='+', vert=1, whis=1.5)
	pl.setp(bp['boxes'], color='black')
	pl.setp(bp['whiskers'], color='black')
	pl.setp(bp['fliers'], color='red', marker='+')

	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)

	ax1.set_axisbelow(True)
	ax1.set_title('BW-R Miss-Rate Distribution with Three Co-Runners', fontsize = pl_fontsize)
	ax1.set_xlabel('Percentage Utilization', fontsize = pl_fontsize)
	ax1.set_ylabel('Miss-Rate', fontsize = pl_fontsize)

	ax1.set_xlim(0.5, 7 + 0.5)
	top = 35 
	bottom = -2
	ax1.set_ylim(bottom, top)
	xtickNames = pl.setp(ax1, xticklabels = utilization)
	pl.setp(xtickNames, rotation = 45, fontsize = pl_fontsize)

	numBoxes = 7
	boxColors = ['darkkhaki', 'darkkhaki']
	medians = list(range(numBoxes))
	for i in range(numBoxes):
	    box = bp['boxes'][i]
	    boxX = []
	    boxY = []
	    for j in range(5):
	        boxX.append(box.get_xdata()[j])
	        boxY.append(box.get_ydata()[j])
	    boxCoords = list(zip(boxX, boxY))
	    # Alternate between Dark Khaki and Royal Blue
	    k = i % 2
	    boxPolygon = pl.Polygon(boxCoords, facecolor=boxColors[k])
	    ax1.add_patch(boxPolygon)
	    # Now draw the median lines back over what we just filled in
	    med = bp['medians'][i]
	    medianX = []
	    medianY = []
	    for j in range(2):
	        medianX.append(med.get_xdata()[j])
	        medianY.append(med.get_ydata()[j])
	        pl.plot(medianX, medianY, 'k')
	        medians[i] = medianY[0]
	    # Finally, overplot the sample averages, with horizontal alignment
	    # in the center of each box
	    pl.plot([np.average(med.get_xdata())], [np.average(parsed_miss_data[i])],
	             color='w', marker='*', markeredgecolor='k')  

	pos = np.arange(7) + 1
	boxColors = ['red', 'green']  
	maxs = [np.max(x) for x in parsed_miss_data]
	mins = [np.min(x) for x in parsed_miss_data]  
	upperLabels = [str(np.round(s, 2)) for s in maxs]
	bottomLabels = [str(np.round(s, 2)) for s in mins]
	weights = ['bold', 'semibold']
	for tick, label in zip(range(7), ax1.get_xticklabels()):
	    k = tick % 2
	    ax1.text(pos[tick], top - (top*0.05), upperLabels[tick],
	             horizontalalignment='center', size='small', weight=weights[k], color=boxColors[0])
	    ax1.text(pos[tick], bottom - (bottom*0.25), bottomLabels[tick],
	             horizontalalignment='center', size='small', weight=weights[k], color=boxColors[1])
       
	line_data = []
	for item in range(1, 8, 1):
		line_data.append(np.mean(parsed_miss_data[item - 1]))
		pl.text(item - 0.2, line_data[item - 1], '%.1f' % line_data[item - 1], fontsize = pl_fontsize)

	pl.plot(range(1, 8, 1), line_data, 'r')

	pl.show()

	# Save the figure
	fig.savefig(figname)


	# All done here
	return
  
def main():
	""" This is the primary entry point into the script """

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
		figname = 'Tegra_BW_Mint_Corun_3.png'

		for util in utilization:
			util = str(util)

			# Plot the data one set at a time
			do_set(platform, 'corun', 'mint', part, util, pos)

			# Update the position for the next plot
			pos += 1

		# Draw the box-plots
		do_box_plot(figname, utilization, parsed_miss_data)

	else:
		figname = 'Xeon_BW_' + part.upper() + '.png'

		# Place a title for these plots
		pl.suptitle('Xeon | BW-R | ' + part_size + ' | ' + ws_size + ' | ' + part[0].upper() + part[1:])

		# Plot the data one set at a time
		do_set(platform, 'solo', 'mint', '', part, 1)
		do_set(platform, 'corun', 'mint', '', part, 3)
		do_set(platform, 'solo', 'modf', '', part, 2)
		do_set(platform, 'corun', 'modf', '', part, 4)

	return

# Desginate main as the entry point
if __name__ == "__main__":
	# Call the main function
	main()
