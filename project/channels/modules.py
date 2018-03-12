def channel_to_dict(c):
    dict = {}
    dict['id'] = c.id
    dict['name'] = c.name
    dict['create_date'] = c.create_date
    dict['owner'] = (c.owner).username
    return(dict)
