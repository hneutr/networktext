import ennotator
from webweb import Web

if __name__ == '__main__':
    # filename = 'data/infinite_jest/sections/infinite-jest-section-001.txt'
    # with open(filename, 'r') as f:
    #     content = f.read()
    
    # infinite_jest_store = ennotator.storage.TextDatastore('Infinite Jest')
    # text = ennotator.Ennotator('Asymmetry', '/Users/hne/Desktop/Asymmetry.epub')
    text = ennotator.Ennotator('a_room_with_a_view', '/Users/hne/Desktop/A-Room-with-a-View-morrison.epub')
    text = ennotator.Ennotator('metamorphosis', '/Users/hne/Desktop/Metamorphosis-jackson.epub')

    text.reader.load_entities()
    # text.reader.load_entities(reload=True)

    
    file_name = text.reader.ordered_content_files[-1]

    # print(text.storage.raw_entities[file_name])

    web = Web()
    for file_name in text.reader.ordered_content_files:
        net = ennotator.network.SectionNetwork(text.storage, file_name)
        web.networks.metamorphosis.add_layer(adjacency=net.edges)

    web.display.sizeBy = 'degree'
    web.display.colorBy = 'degree'
    web.show()
    web.save('/Users/hne/Desktop/metamorphosis.html')
