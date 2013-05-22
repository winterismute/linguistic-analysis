#!/usr/bin/env python

# Import from the pattern lib
from pattern.web import Twitter, plaintext
from pattern.en import parse, pprint, split, lemma, Chunk, Word
from pattern.en.wordlist import PROFANITY
from pattern.search import search

# Import from BeautifulSoup, an XML parser used to create the HTML results' page
# src: http://www.crummy.com/software/BeautifulSoup/ 
from BeautifulSoup import BeautifulSoup, Tag, NavigableString

# Some standard python imports
import string
import os
import math

	# Example sentences used for test purposes
#sentence = ' During an attempted robbery a policeman killed a man with a knife . Huh!?'
#sentence2 = 'During an attempted robbery a man with a knife was killed by a nasty policeman. Huh!?'
#sentence3 = 'A man killed a policeman'
#sentence4 = 'A fucking policeman was killed'


# Search list of word used to identify subjects/objects
search_list = ['police', 'policeman', 'policemen']

#list1 = [sentence, sentence2]
#list2 = [sentence3, sentence4]
#results_list.append(list1)
#results_list.append(list2)


def main():

	# First two vars hold the number of relevant sentences, the 2 others the float values
	police_killer_i = 0
	police_killed_i = 0
	police_killer_value = 0.0
	police_killed_value = 0.0
	total_sentences = 0

	# Init Twitter query engine
	engine = Twitter(license=None, language='en')
	results_list = []
	print('Performing twitter queries...')

	# 4 differents queries with 100 results each = 400 results
	results_list.append(engine.search('policeman kill', start=1, count=100, cached=False))
	results_list.append(engine.search('policeman killed', start=1, count=100, cached=False))
	results_list.append(engine.search('police kill', start=1, count=100, cached=False))
	results_list.append(engine.search('police killed', start=1, count=100, cached=False))

	#print lemma('shot')

	# Open a file to put some recognized examples
	examples_file = open('examples.txt', 'w')

	# For each list of results
	for ii in xrange(len(results_list)):
		print('Starting to analyze query results: '+str(ii+1) + ' out of '+str(len(results_list)))
		for res in results_list[ii]:
			# Parse and split the tweet in sentences
			s = parse(string.lower(res.description), chunks=True, relations=True, lemmata=True)
			#s = parse(string.lower(res), chunks=True, relations=True, lemmata=True)
			#pprint(s)
			
			ss = split(s)

			# Then for each sentence
			for sent in ss:
				# Update sentences number
				total_sentences += 1

				found = False
				i = 0
				value = 0.0

				# First check the affidability of the sentence - .5 if a bad word is found, 1.0 otherwise
				while (not found and (i < len(sent.words))):
					#print sent.words[i]
					if (sent.words[i].string in PROFANITY):
						found = True
					i = i+1
				if (found):
					#print('Found a bad word')
					value = 0.5
				else:
					# No bad words found -> giving max affidability value
					value = 1.0

				#print sent.chunks
				# Here, I want to clear the sentence from the PNP elements. I will filter out the words belonging to PNP from the list
				cleared_sentence_words = filter( lambda(i): i.pnp is None, sent.words)
				cleared_string = '';

				# But now, seems like there's no way to reconstruct a parsed sentence but assembling again a string and parsing it again
				for word in cleared_sentence_words:
					cleared_string += ' ' + word.string
				#print cleared_string
				cleared_sentence = parse(cleared_string, chunks=True, relations=True, lemmata=True)
				cleared_sentence = split(cleared_sentence)
				#pprint(cleared_sentence)
				sentence_type1 = False

				# Now cleared sentence is a sentence without PNP
				# Check if it is a standard active sentence
				for match in search('NP kill NP', cleared_sentence):
					# It is
					sentence_type1 = True
					# Check if the Subject is the police
					if (match.constituents()[0].role == 'SBJ'):
						for word in match.constituents()[0].words:
							if word.string in search_list:
								police_killer_i += 1
								police_killer_value += value
								#print('Police killed')
								# Print to the examples' file the recognized match
								for sword in match.words:
									examples_file.write(str(sword.string.encode("utf-8"))+' ')
								examples_file.write('\r\n')
								#examples_file.write(str(match.words)+'\r\n');
								examples_file.write('   Recognized as: police killed somebody'+'\r\n')
								examples_file.write('   TYPE: ACTIVE - SUBJECT'+'\r\n')
								examples_file.write('\r\n')

					if (len(match.constituents()) > 2):
						# Or check if it is object
						if (match.constituents()[2].role == 'OBJ'):
							for word in match.constituents()[2].words:
								if word.string in search_list:
									police_killed_i += 1
									police_killed_value += value
									#print('Killed by police')
									# Print to the example file the recognized match
									for sword in match.words:
										examples_file.write(str(sword.string.encode("utf-8"))+' ')
									examples_file.write('\r\n')
									examples_file.write('   Recognized as: police killed by somebody'+'\r\n')
									examples_file.write('   TYPE: ACTIVE - OBJECT'+'\r\n')
									examples_file.write('\r\n')

				# If it was not an active sentence, check if it is a passive one
				if (not sentence_type1):
					#print('Try type 2')
					for match in search('NP kill (PP)+ (NP)+', cleared_sentence):
						# Here, the problem is that match.constituents returns a mixed list which can contain both Chunks and Words
						# We are interested in tags, hence in Chunks, hence we need to do some isinstance non-safe tricks
						# Checking the subject
						if (isinstance(match.constituents()[0], Chunk)):
							if (match.constituents()[0].role == 'SBJ'):
								#print('Is subject')
								for word in match.constituents()[0]:
								#for word in match.chunks()[0]:
									if word.string in search_list:
										police_killer_i += 1
										police_killer_value += value
										# Print to the example file the recognized match
										for sword in match.words:
											examples_file.write(str(sword.string.encode("utf-8"))+' ')
										examples_file.write('\r\n')
										examples_file.write('   Recognized as: police killed somebody'+'\r\n');
										examples_file.write('   TYPE: PASSIVE - SUBJECT - CHUNK'+'\r\n')
										examples_file.write('\r\n');

						elif (isinstance(match.constituents()[0], Word)):
							if match.constituents()[0].string in search_list:
								police_killer_i += 1
								police_killer_value += value
								#print('Killed by police')
								# Print to the example file the recognized match
								for sword in match.words:
									examples_file.write(str(sword.string.encode("utf-8"))+' ')
								examples_file.write('\r\n')
								examples_file.write('   Recognized as: police killed somebody'+'\r\n')
								examples_file.write('   TYPE: PASSIVE - SUBJECT - WORD'+'\r\n')
								examples_file.write('\r\n')

						# Checking the object. First I have to filter out the Word objects from the match results to see if I have enough Chunks
						if (len( filter(lambda(i): isinstance(i, Chunk), match.constituents())) == 4):
							if (match.constituents()[3].role == 'OBJ'):
								for word in match.constituents()[3]:
									if word.string in search_list:
										police_killed_i += 1
										police_killed_value += value
										# Print to the example file the recognized match
										for sword in match.words:
											examples_file.write(str(sword.string.encode("utf-8"))+' ')
										examples_file.write('\r\n')
										examples_file.write('   Recognized as: police was killed by somebody'+'\r\n');
										examples_file.write('   TYPE: PASSIVE - OBJECT - CHUNK'+'\r\n')
										examples_file.write('\r\n');

	# Some math
	value_killer = 0.0
	value_killer = math.floor( (police_killer_value / total_sentences) * 100.0)
	value_killed = 0.0
	value_killed = math.floor(( police_killed_value / total_sentences) * 100.0)
	value_unc = 100.0 - ( (police_killer_i + police_killed_i) / float(total_sentences) * 100.0)
	examples_file.flush();

	print('Total sentences: ' +str(total_sentences))
	print('Value police killer: '+str(value_killer))
	print('Value police killed: '+str(value_killed))

	print('Creating the HTML page with results..')

	# Shape the Url of the char image, using the old Google char API
	# docs: http://code.google.com/intl/it-IT/apis/chart/image/docs/making_charts.html
	chart_url = 'http://chart.apis.google.com/chart?chxl=0:|Policeman+Death|Killed+by+police&chxs=0,676767,11.5,0,lt,676767&chxt=x&chbh=a,100&chs=300x200&cht=bvg&chco=FF0000&chd=t:'
	chart_url += str(value_killed)
	chart_url += ','
	chart_url += str(value_killer)
	chart_url += '&chtt=Twitter+Analysis+Chart'

	#http://chart.apis.google.com/chart?chxl=0:|Policeman+Killed|Killed+by+police&chxs=0,676767,11.5,0,lt,676767&chxt=x&chbh=a,100&chs=300x200&cht=bvg&chco=FF0000&chd=t:30,70&chtt=Twitter+Analysis+Chart

	# Now, create a HTML page with the information
	#  The paga is simple: head with title, body with a big div holding an image (the chart) and 5 additional divs with text
	htmldata = BeautifulSoup()

	htmltag = Tag(htmldata, "html")
	headtag = Tag(htmldata, "head")

	titletag = Tag(htmldata, "title")
	titletag.insert(0, NavigableString('Twitter Stream Analysis Example'))

	bodytag = Tag(htmldata, "body")

	imgtag = Tag(htmldata, "img")
	imgtag['src'] = chart_url

	divtag_wrap = Tag(htmldata, "div")
	divtag_t1 = Tag(htmldata, "div")
	divtag_t1.insert(0, NavigableString('Total sentences analyzed: '+str(total_sentences)+' taken from 400 public tweets'))

	divtag_t2 = Tag(htmldata, "div")
	divtag_t2.insert(0, NavigableString('Total percentage of sentences that seem to refer to a policeman killed: '+str(int(value_killed))+'%'))

	divtag_t3 = Tag(htmldata, "div")
	divtag_t3.insert(0, NavigableString('Total percentage of sentences that seem to refer to a death caused by police: '+str(int(value_killer))+'%'))

	divtag_t4 = Tag(htmldata, "div")
	divtag_t4.insert(0, NavigableString('Total percentage of NOT USEFUL data: '+str(int(value_unc))+'%'))

	divtag_t5 = Tag(htmldata, "div")
	divtag_t5.insert(0, NavigableString('NOTE: The chart takes into account also the simple affidability criteria'))

	htmldata.insert(0, htmltag)
	htmltag.insert(0, headtag)
	headtag.insert(0, titletag)

	htmltag.insert(1, bodytag)

	bodytag.insert(0, divtag_wrap)
	divtag_wrap.insert(0, imgtag)
	divtag_wrap.insert(1, divtag_t1)
	divtag_wrap.insert(2, divtag_t2)
	divtag_wrap.insert(3, divtag_t3)
	divtag_wrap.insert(4, divtag_t4)
	divtag_wrap.insert(5, divtag_t5)

	#print(htmldata)

	#write HTML data to a file - prettify makes the HTML code more readable
	htmlfile = open('results.html', 'w')
	#htmlfile.write(htmldata.encode("utf-8"))
	htmlfile.write(htmldata.prettify())
	htmlfile.flush()
	htmlfile.close()

	examples_file.close()

	# We are done. Finally!
	print('Done. Results written to results.html. Exiting...')

# Call the "main" function when running this script
if __name__ == '__main__': main()
