import sys, getopt
import os
import re

# Import data from sub-scripts
from mem_colors_single import *
from mem_plots import *


# Global Data
allowed_cli_arguments = {}

# Set master debug control
master_debug = False

# Parse the data in the dictionary file to get acceptable values of CLI arguments
def build_global_data():

	# Initialize the lists in allowed arguments dictionary
	allowed_cli_arguments["platforms"]	= []
	allowed_cli_arguments["benchmarks"]	= []
	allowed_cli_arguments["linux_types"]	= []
	allowed_cli_arguments["buddy_types"]	= []
	allowed_cli_arguments["data_types"]	= []
	allowed_cli_arguments["corunners"]	= []
	allowed_cli_arguments["utilizations"]	= []

	# Open the input file
	with open('CLI.log', 'r') as fdi:
		for line in fdi:
			if 'Platform' in line:
				platforms = re.match(r'^Platform[\t]+: (.*)$', line)
				allowed_cli_arguments["platforms"]	=  [x for x in platforms.group(1).split(',')]
			elif 'Benchmark' in line:
				benchmarks = re.match(r'^Benchmark[\t]+: (.*)$', line)
				allowed_cli_arguments["benchmarks"]	=  [x for x in benchmarks.group(1).split(',')]
			elif 'Linux' in line:
				linux_types = re.match(r'^Linux[\t]+: (.*)$', line)
				allowed_cli_arguments["linux_types"]	=  [x for x in linux_types.group(1).split(',')]
			elif 'Buddy' in line:
				buddy_types = re.match(r'^Buddy[\t]+: (.*)$', line)
				allowed_cli_arguments["buddy_types"]	=  [x for x in buddy_types.group(1).split(',')]
			elif 'Data' in line:
				data_types = re.match(r'^Data[\t]+: (.*)$', line)
				allowed_cli_arguments["data_types"]	=  [x for x in data_types.group(1).split(',')]
			elif 'Corun' in line:
				corunners = re.match(r'^Corun[\t]+: (.*)$', line)
				allowed_cli_arguments["corunners"]	=  [x for x in corunners.group(1).split(',')]
			elif 'Utilization' in line:
				utilizations = re.match(r'^Utilization[\t]+: (.*)$', line)
				allowed_cli_arguments["utilizations"]	=  [x for x in utilizations.group(1).split(',')]

	# Sanity Check - Make sure that all the CLI lists have been populated
	for cli_key, cli_list in allowed_cli_arguments.items():
		if cli_list == []:
			print "CLI Argument [%s] has no valid values. Please update \'CLI.log\' file!" % (cli_key)
			sys.exit()

	# All the CLI lists have been successfully built. Return to caller
	return


# Create a main function for this program
def main(argv):

	# Create an internal help function for printing help information
	def help():
		
		print 'profile.py -p <platform> -b <benchmark> -l <linux> -a <buddy> -d <data> -c <corun> -u <utilization>'
		print 'For further detail about the CLI arguments, please consult \'nomenclature.txt\' file'

		return

	# Create another internal helper function for updating the default values of CLI arguments after
	# error checking
	def update_defaults(arg_list, value):
		if (value not in allowed_cli_arguments[arg_list]):
			print "Invalid Value [%s] passed for CLI Argument [%s]."  % (value, arg_list)
			print "Please see / update \'CLI.log\' file for a list of permissable CLI argument values!" 
			sys.exit()

		return value

	# Assign default values to command line arguments
	platform 	= 'TG'		# Default Platform	: Tegra
	benchmark	= 'BW'		# Default Benchmakr	: Bandwdith - Read
	linux 		= 'UN'		# Default Linux		: PALLOC Patched
	buddy		= 'PL'		# Default Allocator	: Buddy + PALLOC
	data		= 'PF'		# Default Data		: Perf Data
	corun		= '00'		# Default Co-runners	: Solo
	utilization	= '100'		# Default Utilization	: 100%

	# Now get any modified values from command line
	try:
		opts, args = getopt.getopt(argv, "hp:b:l:a:d:c:u:o:", [ "platform=", 	\
					    				"benchmark=", 	\
					    				"linux=", 	\
					    				"buddy=", 	\
					    				"data=",	\
					    				"corun=",	\
					    				"utilization="])

	except:
		help()
		sys.exit(2)

	# Before parsing the CLI arguments, build the dictionary of allowed CLI values
	build_global_data()

	# Parse the passed in input parameters
	for opt, arg in opts:
		if opt == '-h':
			help()
			sys.exit()
		elif opt in ("-p", "--platform"):
			platform = update_defaults('platforms', arg)
		elif opt in ("-b", "--benchmark"):
			benchmark = update_defaults('benchmarks', arg)
		elif opt in ("-l", "--linux"):
			linux = update_defaults('linux_types', arg)
		elif opt in ("-a", "--buddy"):
			buddy = update_defaults('buddy_types', arg)
		elif opt in ("-d", "--data"):
			data = update_defaults('data_types', arg)
		elif opt in ("-c", "--corun"):
			corun = update_defaults('corunners', arg)
		elif opt in ("-u", "--utilization"):
			utilization = update_defaults('utilizations', arg)

	# Print out the values given to the parameters
	if master_debug:
		print "Platform    : ", platform
		print "Benchmark   : ", benchmark
		print "Linux       : ", linux
		print "Buddy       : ", buddy
		print "Data        : ", data
		print "Corun       : ", corun
		print "Utilization : ", utilization

	# Create the name of the parent directory based on CLI arguments
	parent_dir = '../data/%s/%s/%s/%s/%s/%s/%s/' % (platform, benchmark, linux, buddy, data, corun, utilization)

	if not os.path.isdir(parent_dir):
		print 'Provided CLI arguments do not constitute a valid path to data directory!'
		print 'Path : %s' % (parent_dir)
		sys.exit()

	if data == 'CL':
		# Plot the data regarding the standard deviation of colors
		pdf_clr_std_hash = do_clr_pdf(parent_dir, True)

	if data == 'PF':
		# Plot the box plots for all utilizations
		parent_dir = '../data/%s/%s/%s/%s/%s/%s/' % (platform, benchmark, linux, buddy, data, corun)
		do_performance_boxplots(parent_dir, False)

	# All done
	return

if __name__ == "__main__":
	# Invoke the main function
	main(sys.argv[1:])
