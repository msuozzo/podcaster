from podcaster.table import TextTable


def build_data_rows(ind_to_key, obj_lst, *series_args):
    """

    *series_args: 3-tuples of (series_name, obj_to_data, data_to_str)
        where the latter two elements are functions converting each object to
        data and the data to a string, respectively.
    """
    rows = [['CMD'] + [name for name, _, _ in series_args]]
    for ind, obj in enumerate(obj_lst):
        row = [ind_to_key(ind)] + [fmt(extract(obj)) for _, extract, fmt in series_args]
        rows.append(row)
    return rows


def build_menu(title, data_rows, action_rows):
    menu = TextTable()

    # Add table title
    menu.add_break_row(seps=('+', '+'))
    menu.add_row((title,), align='c', seps=('|', '|'))
    menu.add_break_row(seps=('+', '+'))

    # Add data section
    num_series = len(data_rows[0]) - 2
    name_seps = ('|', '|') + num_series * ('|',) + ('|',)
    header_seps = ('+', '+') + num_series * ('v',) + ('+',)
    data_seps = ('|', '|') + num_series * (' ',) + ('|',)
    footer_seps = ('+', '+') + num_series * ('^',) + ('+',)
    menu.add_row(data_rows[0], align='c', seps=name_seps)
    menu.add_break_row(seps=header_seps)
    menu.set_seps(*data_seps)
    for data_row in data_rows[1:]:
        menu.add_row(data_row)
    if len(data_rows) == 1:
        menu.add_row(('There\'s nothing here...',), seps=('?', '?'))
    menu.add_break_row(seps=footer_seps)

    # Add action section
    menu.set_seps('|', '|', '|')
    for action_row in action_rows:
        menu.add_row(action_row)
    menu.add_break_row(seps=('+', '+', '+'))

    return str(menu)
