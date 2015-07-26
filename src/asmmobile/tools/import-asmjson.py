#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2015  Assembly Organizing
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import dateutil.parser
import re


def normalizeShortNameEn(name):
    result = name.replace("ARTtech seminars - ", "Seminar, ")
    result = result.replace("ARTtech seminars: ", "Seminar: ")
    return result


def normalizeShortNameFi(name):
    result = name.replace("ARTtech seminars - ", "Seminaari, ")
    result = result.replace("ARTtech seminars: ", "Seminaari: ")
    return result


def escapeDescription(description):
    escaped = description
    escaped = escaped.replace("> ", "> <!---->")
    escaped = escaped.replace(" <", " <!----><")
    # Common mistake where & is not escaped in descriptions.
    escaped = re.sub("& ", "&amp; ", escaped)
    return escaped


def importer(filename, prefix):
    fp = open(filename, "r")
    data = json.load(fp)

    locations = {}
    events = {}

    for lang in ['en', 'fi']:
        if lang not in locations:
            locations[lang] = {}
        if lang not in events:
            events[lang] = {}

    order_id = 0
    for location_key, location in data['locations'].items():
        location_name_en = location.get('name')
        location_name_fi = location.get('name_fi', location_name_en)

        location_description_en = location.get("description")
        location_description_fi = location.get(
            "description_fi", location_description_en)

        location_url = location.get("url")
        locations['en'][location_key] = {
            'name': location_name_en,
            'url': location_url,
            'description': location_description_en
        }
        locations['fi'][location_key] = {
            'name': location_name_fi,
            'url': location_url,
            'description': location_description_fi
        }

    for event in data['events']:
        # Ignore empty entries:
        if event['name'] == "" or event.get('name_fi', "") == "":
            continue

        event_id = event["key"]

        name_en = event["name"]
        name_fi = event.get("name_fi", name_en)
        location_key = event.get('location_key')
        description_en = event.get('description', u"")
        description_fi = event.get("description_fi", description_en)
        url = event.get("url")
        start_time = dateutil.parser.parse(event.get("start_time"))
        end_time_str = event.get("end_time")
        end_time = None
        if end_time_str:
            end_time = dateutil.parser.parse(end_time_str)
        start_original = event.get("original_start_time")
        is_major = 'major' in event.get('flags', [])
        is_canceled = 'canceled' in event.get('flags', [])
        categories = []
        if is_major:
            categories.append("Major_event")
        categories.extend(event.get('categories', []))

        events['en'][event_id] = {
            'name': name_en,
            'url': url,
            'start': start_time,
            'start-original': start_original,
            'end': end_time,
            'location': location_key,
            'categories': categories,
            'is-major': is_major,
            'description': escapeDescription(description_en),
            'canceled': is_canceled,
            'order': order_id,
            'short-name': normalizeShortNameEn(name_en),
            }
        events['fi'][event_id] = {
            'name': name_fi,
            'url': url,
            'start': start_time,
            'start-original': start_original,
            'end': end_time,
            'location': location_key,
            'categories': categories,
            'is-major': is_major,
            'description': escapeDescription(description_fi),
            'canceled': is_canceled,
            'order': order_id,
            'short-name': normalizeShortNameFi(name_fi),
            }
        order_id += 1

    return locations, events
