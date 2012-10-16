interwiki
=========

Script for analyzing interwiki links from Wikipedia. 

Given wikipedias for English and language X (currently hardcoded to Latvian),
this script will prepare a list of articles that:

 * have more than 50 interwiki links in English wikipedia
 * have no corresponding article in language X wikipedia

This tool can be used to come up with priorities--which articles to write 
first!

Usage
=====

Invoke the script like this:

    python process.py [title_of_category]

Or better:

    pypy process.py [title_of_category] 

Use the optional title_of_category argument to limit scope of articles 
inspected. Only articles that belong to given category or its subcategories 
(up to 2nd level) will be inspected. Be aware that use of this parameter 
significantly increases run time of the script. 

Output
======

Upon completion the script writes file "titles.txt". This is a text file, 
and each line has the following format:

    num_interwiki_links | title_en | title_x | article_size_bytes

Example output, last few lines from output:

    227 | Spain | Spānija | 73045
    229 | Africa | Āfrika | 30132
    235 | Europe | Eiropa | 33245
    236 | Germany | Vācija | 105321
    237 | Wikipedia | Vikipēdija | 17636
    242 | United_States | Amerikas Savienotās Valstis | 111834
    243 | True_Jesus_Church | Patiesā Jēzus baznīca | 12985
    245 | Russia | Krievija | 99812

Data Files
==========

The script uses wikipedia database dump files (.sql.gz) from

    http://download.wikimedia.org/enwiki/latest/

and

    http://download.wikimedia.org/enwiki/latest/
    
It checks for required files on startup and optionally downloads them.
Be aware that some of the required files are big, totalling ~2.3GB

