# -*- coding: UTF-8 -*-

""" Find wikipedia articles with more than 50 interwiki links. """

import gzip
import os
import re
import sys
import urllib

# data files come from here:
EN_DUMPS_ROOT = 'http://download.wikimedia.org/enwiki/latest/'
CATEGORYLINKS_FILENAME = 'enwiki-latest-categorylinks.sql.gz'
LANGLINKS_FILENAME = 'enwiki-latest-langlinks.sql.gz'
PAGE_FILENAME = 'enwiki-latest-page.sql.gz'

LV_DUMPS_ROOT = 'http://download.wikimedia.org/lvwiki/latest/'
LV_PAGE_FILENAME = 'lvwiki-latest-page.sql.gz'
ITERATIONS = 3

# Regex pattern to match stuff like "'Thirty Years\' War'"
# Basically, match strings enclosed in apostrophes, and allow
# strings to contain escaped apostrophes.
SM = r"'((?:\\'|[^'])*)'"
# Non-matching version
NSM = r"'(?:\\'|[^'])*'"

print "usage: python process.py [<category_title>]"

root_category = None
if len(sys.argv) == 2:
    root_category = sys.argv[1]


# Check presence of input files
for root, filename in [(EN_DUMPS_ROOT, CATEGORYLINKS_FILENAME),
                       (EN_DUMPS_ROOT, LANGLINKS_FILENAME),
                       (EN_DUMPS_ROOT, PAGE_FILENAME),
                       (LV_DUMPS_ROOT, LV_PAGE_FILENAME)]:
    if not os.path.exists(filename):
        s = "File '%s' not found. Download? (y/n) " % filename
        user_says = raw_input(s)
        url = "%s%s" % (root, filename)
        if user_says.lower() == "y":
            def progress(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write("%2d%%" % percent)
                sys.stdout.write("\b\b\b")
                sys.stdout.flush()

            print "Downloading %s ... " % url,
            urllib.urlretrieve(url, filename, reporthook=progress)
            print ""

        else:
            print "Please download %s" % url
            sys.exit(1)


def read_gzip_with_progress(filename, expected_line_count=10000):
    """Yield lines from text file, print progress information to stdout. """

    batch_size = int(expected_line_count / 100)

    line_no = 0
    fileobj = gzip.GzipFile(filename)
    while True:
        line = fileobj.readline()
        if line == "":
            break
        line_no += 1
        if line_no % batch_size == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

        yield line

    print "\nLines read: %d" % line_no


def get_page_ids_for_category(category_title, depth=ITERATIONS):
    """

    Get a set of page ids we're interested in. These are the pages
    that belong to root_category or any of its subcategories.
    We do this in iterations. In each iteration we pick page ids,
    look up their namespaces and titles, and extend our category set
    and page id set. We stop when either all qualifying page ids are found
    or iteration count limit is reached.

    """

    subcategory_titles = set([root_category])
    page_ids = set([])

    print "Searching for subcategories of '%s'..." % root_category

    newfound_subcategories = ["dummy"]
    iteration = 0
    while newfound_subcategories and iteration < ITERATIONS:
        iteration += 1
        print "Iteration %d" % iteration
        possible_category_ids = set([])
        newfound_subcategories = []
        parent_titles = {}

        # Matched pattern example: (1234,      'Sports')
        #                           page_id     category_title
        five_string_fields = ",".join([NSM for i in range(0, 5)])
        prog = re.compile("\((\d+),%s,%s\)" % (SM, five_string_fields))
        for line in read_gzip_with_progress(CATEGORYLINKS_FILENAME, 6956):

            for page_id, category_title in re.findall(prog, line):
                page_id = int(page_id)
                # If this page to belongs to one of the categories we're
                # interestend in and it hasn't been already marked as
                # qualifying...
                if category_title in subcategory_titles:
                    if page_id not in page_ids:
                        # we mark it as qualifying
                        page_ids.add(page_id)
                        # and add it to the set of possible categories that
                        # we'll have to check and look up titles for in next
                        # step
                        possible_category_ids.add(page_id)
                        parent_titles[page_id] = category_title

        tmpl = "After parsing categorylinks got %d new qualifying page ids"
        print tmpl % len(possible_category_ids)

        # Look up namespaces and titles for page_ids
        # in "possible_category_ids" set
        # Matched pattern example: (123,              0, 'Dzeltenā Jūra'
        #                           article_id namespace  english_title
        prog = re.compile("\((\d+),(\d+),%s" % SM)
        for line in read_gzip_with_progress(PAGE_FILENAME, 2212):
            for article_id, namespace, title in re.findall(prog, line):
                article_id = int(article_id)
                if article_id in possible_category_ids and namespace == "14":
                    # It's a category! Add it to our subcategory titles
                    subcategory_titles.add(title)
                    title_pair = "%s->%s" % (parent_titles[article_id], title)
                    newfound_subcategories.append(title_pair)

        print "Found subcategories: %s" % ", ".join(newfound_subcategories)
    return page_ids

qualifying_page_ids = None
if root_category is not None:
    qualifying_page_ids = get_page_ids_for_category(root_category)

print "Counting links..."

# Matched pattern example: (1234,      'lv',          'Dzeltenā Jūra')
#                           article_id language_code  translated_title
prog = re.compile("\((\d+),'(\w+)',%s\)" % SM)
counts = {}
lv_article_titles = {}
found_ids = set([])

for line in read_gzip_with_progress(LANGLINKS_FILENAME, 499):
    for article_id, lang_code, title in re.findall(prog, line):

        article_id = int(article_id)
        if qualifying_page_ids is not None:
            if article_id not in qualifying_page_ids:
                # This article is not in any of the categories we're interested
                # in, so skip.
                continue

        if lang_code == "lv":
            lv_article_titles[article_id] = title

        counts[article_id] = counts.get(article_id, 0) + 1
        # Use "==" instead of ">=" so each article is counted exactly once.
        if counts[article_id] == 49:
            found_ids.add(article_id)

# At this point we don't need the big qualifying_page_ids
# set any more, so let's reclaim some memory
qualifying_page_ids = None

print "Looking up Latvian page sizes"

lv_article_sizes = {}
lv_titles_inverse = {}
for article_id, title in lv_article_titles.items():
    title_underscores = title.replace(" ", "_")
    lv_titles_inverse.setdefault(title_underscores, []).append(article_id)

prog = re.compile("\(\d+,(\d+),%s,[^)]*,(\d+),\d+,[^,]+\)" % SM)
# Matched pattern example: (1,  0,        'Dzeltenā Jūra', 9300)
#                           id, namespace lv_title         size

for line in read_gzip_with_progress(LV_PAGE_FILENAME):
    for namespace, title, size in re.findall(prog, line):
        if namespace != "0":
            # Only consider articles in "default" namespace
            continue

        if title in lv_titles_inverse:
            for article_id in lv_titles_inverse[title]:
                lv_article_sizes[article_id] = int(size)

print "Looking up titles..."

# Matched pattern example: (123,              0, 'Dzeltenā Jūra'
#                           article_id namespace  english_title
prog = re.compile("\((\d+),(\d+),%s" % SM)
lines = []
skipped = 0
line_no = 0
for line in read_gzip_with_progress(PAGE_FILENAME, 2212):
    for article_id, namespace, title in re.findall(prog, line):
        article_id = int(article_id)

        if namespace != "0":
            skipped += 1
            continue

        if article_id in found_ids:
            lines.append((counts[article_id],
                          title,
                          lv_article_titles.get(article_id, "---"),
                          lv_article_sizes.get(article_id, "---")))

lines.sort()
out = open('titles.txt', 'w')
for count, title_en, title_lv, size in lines:
    title_en = title_en.replace(r"\'", "'")
    title_lv = title_lv.replace(r"\'", "'")
    out.write("%d | %s | %s | %s\n" % (count, title_en, title_lv, size))

out.close()

print "Done, titles saved in file 'titles.txt'."
print "Skipped %d titles." % skipped
