#!/usr/bin/env python3

import json
import sys
import os
import getopt
import shutil
from datetime import datetime, timedelta


def usage():
    print('usage: {} OPTIONS'.format(sys.argv[0]))
    print('OPTIONS:')
    print('\t-h|--help\t\tdisplay this usage')
    print('\t-r|--repo REPO\t\trepo to load comments by utteranc.es ( owner/repo_name )')
    print('\t-f|--file FILE\t\tissue json file which generated by jrdeng/query-issues-action')
    print('\t-d|--dir POST_DIR\thugo post dir to store *.md files')


def log_error_and_exit(msg):
    print(msg)
    exit(2)


def normalize_issue_title(title):
    r = title.replace('/', '_').strip('., ')
    return r


def datetime_to_beijing(iso_str):
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
    return (dt + timedelta(hours=8)).isoformat()


def write_hugo_header(md, issue):
    md.write('---\n')
    md.write('title: "{}"\n'.format(issue['title'].replace("\"", "\\\"")))
    md.write('date: {}+08:00\n'.format(datetime_to_beijing(issue['createdAt'])))
    md.write('slug: "{}"\n'.format(issue['number']))
    if len(issue['labels']) > 0:
        md.write('tags: [\n') # tags begin
        for label in issue['labels']:
            md.write('    "{}",\n'.format(label))
        md.write(']\n') # tags end
    md.write('---\n\n')


def write_hugo_body(md, issue):
    md.write('{}\n\n'.format(issue['body']))


def write_comments(md, owner, repo, issue):
    md.write('<hr style="width: 100%"/>\n\n')
    md.write('<h1 style="font-size: 1.5em;color:#555;font-weight: bold;">Comments: (on <a href="{}">github issue)</a></h1>\n\n'.format(issue['url']))

    # write comments using utteranc.es~
    comment_template = '''
<script src="https://utteranc.es/client.js"
        repo="{}/{}"
        issue-number="{}"
        theme="github-light"
        crossorigin="anonymous"
        async>
</script>
'''
    md.write(comment_template.format(owner, repo, issue['number']))


def generate_hugo_post(owner, repo, issue_list, output_dir):
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir, True)
    os.mkdir(output_dir) 
    for issue in issue_list:
        #print('processing issue:\n{}'.format(issue))
        file_name = '{}_{}.md'.format(issue['number'], normalize_issue_title(issue['title']))
        with open('{}{}{}'.format(output_dir, os.sep, file_name), 'w+') as md:
            write_hugo_header(md, issue)
            write_hugo_body(md, issue)
            write_comments(md, owner, repo, issue)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hr:f:d:', ['help', 'repo=', 'file=', 'dir='])
    except getopt.GetoptError as err:
        usage()
        log_error_and_exit(err)
    owner = None
    repo = None
    input_file = None
    post_dir = None
    for o, a in opts:
        if o == '-h':
            usage()
            exit()
        elif o in ('-r', '--repo'):
            kv = a.split('/')
            if len(kv) == 2:
                owner = kv[0] if kv[0] != 'undefined' else None
                repo = kv[1] if kv[1] != 'undefined' else None
        elif o in ('-f', '--file'):
            input_file = a if a != '' else None
        elif o in ('-d', '--dir'):
            post_dir = a if a != '' else None
        else:
            usage()
            assert False, 'unhandled option'

    if owner is None or repo is None:
        usage()
        log_error_and_exit('owner/repo_name must be set via -r')
    if input_file is None:
        usage()
        log_error_and_exit('issue json file must be set via -f')
    if post_dir is None:
        usage()
        log_error_and_exit('post_dir must be set via -d')

    issue_list = None
    with open(input_file) as issues_json_file:
        issue_list = json.load(issues_json_file)

    if issue_list is None:
        print('failed to load issues json')
        exit()

    generate_hugo_post(owner, repo, issue_list, post_dir)


if __name__ == '__main__':
    main()
    print('DONE')
