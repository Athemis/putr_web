import re
import time
import html

from jinja2 import Environment, PackageLoader

class HTMLWriter():
    def __init__(self):
        self.env = Environment(loader=PackageLoader('putr_web', 'templates'))

    def render_template(self, tpl_filename, content):
        return self.env.get_template(tpl_filename).render(content)

    def create_index_html(self, content):
        filename = "index.html"
        with open(filename, 'w') as f:
            html = self.render_template('content.html', content)
            f.write(html)



class PutrParser():
    def __init__(self, filename):
        self.prefix = None
        self.data = []
        self.categories = []
        self.load_file(filename)
        self.parse_data()

    def load_file(self, filename):
        try:
            with open(filename, 'r') as f:
                self.data = f.read().splitlines()
        except IOError:
            raise


    def find_item(self, line):
        if '----------------------------------------' in line:
            return True

    def parse_item_type(self, line, item):
        types = {'relation': 'RELATION',
                 'node': 'NODE:',
                 'way': 'WAY'}
        for key in types:
            if line.startswith(types[key]):
                re_id = re.search('(\d+)', line)
                re_name = re.search('\(([^)]+)\)', line)
                item.id = re_id.group(0)
                item.type = key
                try:
                    item.name = re_name.group(1)
                except AttributeError:
                    print('Item has no name!')
                print("Found item of type {} with ID {}".format(key, item.id))
                # No need to search the other keys as we already scored a hit
                return True
        return False

    def parse_message(self, line):
        if not line.startswith('='):
            re_content = re.search('(\w+): (.+)', line)
            try:
                num_groups = len(re_content.groups())
            except AttributeError:
                num_groups = 0

            if num_groups == 2:
                message = re_content.group(2).strip()
                msg_type = re_content.group(1).strip()
            else:
                message = line.strip()
                msg_type = 'LAST'

            return {'msg_type': msg_type,
                    'text': html.escape(message, quote=True)}
        else:
            return None

    def parse_item(self, item, last_item, line):
        found_item_type = self.parse_item_type(line, item)

        if not found_item_type:
            message = self.parse_message(line)
            if message is not None:

                if message['msg_type'] == 'LAST':
                    if last_item.last_added == 'ERR':
                        last_item.errors[-1] = "{} {}".format(last_item.errors[-1], message['text'])
                        # append_to = item.errors
                    else:
                        last_item.notes[-1] = "{} {}".format(last_item.notes[-1], message['text'])
                        # append_to = item.notes
                else:
                    last_item.last_added = message['msg_type']
                    if message['msg_type'] == 'ERR':
                        item.errors.append(message['text'])
                    elif message['msg_type'] == 'NOTE':
                        item.notes.append(message['text'])



    def parse_data(self):
        found_categories = []

        category = None
        item = None

        categories = {'stop_areas': 'Stop Areas',
                      'route_masters': 'Route Masters',
                      'unclassified_routes': 'Classify Routes',
                      'ptv1_routes': 'PTv1 Routes',
                      'ptv2_routes_1': 'PTv2 Routes 1',
                      'ptv2_routes_2': 'PTv2 Routes 2',
                      'ptv2_routes_3': 'PTv2 Routes 3',
                      'ptv2_routes_4': 'PTv2 Routes 4',
                      'multipolygons': 'Analyze MPs',
                      'ways': 'Analyze Ways',
                      'nodes': 'Analyze Nodes',
                      'tour_ways': 'Extract Tour Ways',
                      'platforms': 'Analyze Platforms',
                      'incomplete_stop_areas': 'Incomplete stop_areas'}

        for line in self.data:
            if line:
                if category:
                    if self.find_item(line):
                        print("Found new item")
                        item = PutrItem()
                    elif item:
                        if len(category.items) > 0:
                            last_item = category.items[-1]
                        else:
                            last_item = None
                        self.parse_item(item, last_item, line)
                        category.items.append(item)

                for key in categories:
                    if categories[key] in line:
                        print('Found {}'.format(key))
                        category = PutrCategory(key, categories[key])
                        found_categories.append(category)

        self.categories = found_categories


class PutrCategory():
    def __init__(self, cat_type, name):
        self.type = cat_type
        self.name = name
        self.items = []

    def num_errors(self):
        errors = 0
        for item in self.items:
            errors += item.num_errors()

        return errors

    def num_notes(self):
        notes = 0
        for item in self.items:
            notes += item.num_notes()

        return notes



class PutrItem():
    def __init__(self):
        self.id = None
        self.type = None
        self.name = None
        self.errors = []
        self.notes = []
        self.last_added = None

    def num_errors(self):
        return len(self.errors)

    def num_notes(self):
        return len(self.notes)


def main():
    putr = PutrParser("../putr/dus_putr.err")
    html_writer = HTMLWriter()
    current_time = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    html_writer.create_index_html({'putr': putr,
                                   'time': current_time})


if __name__ == "__main__":
    main()
