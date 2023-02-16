# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/YangCatalog/module-compilation/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                          |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| check\_archived\_drafts.py                                    |      108 |        9 |     92% |121-122, 126-127, 162-165, 169 |
| create\_config.py                                             |        6 |        0 |    100% |           |
| extractors/\_\_init\_\_.py                                    |        0 |        0 |    100% |           |
| extractors/draft\_extractor.py                                |      158 |       51 |     68% |70-72, 90-91, 115-116, 119, 123, 128, 132-151, 159-160, 163, 168, 219-225, 229-242, 245-250 |
| extractors/extract\_elem.py                                   |       57 |       13 |     77% | 40, 86-97 |
| extractors/helper.py                                          |       52 |       29 |     44% |40, 48, 64-84, 97-98, 100-101, 103-104 |
| figures\_and\_stats/\_\_init\_\_.py                           |        0 |        0 |    100% |           |
| figures\_and\_stats/yang\_get\_stats.py                       |      254 |       25 |     90% |122, 134, 150-151, 333-337, 342, 358, 362, 365, 371, 375, 395-397, 399, 422-432 |
| ietf\_modules\_extraction/\_\_init\_\_.py                     |        0 |        0 |    100% |           |
| ietf\_modules\_extraction/gather\_ietf\_dependent\_modules.py |       38 |        7 |     82% |     64-70 |
| ietf\_modules\_extraction/yang\_version\_1\_1.py              |       45 |       11 |     76% |     69-92 |
| job\_log.py                                                   |       63 |       14 |     78% |   104-124 |
| main\_page\_generation/\_\_init\_\_.py                        |        0 |        0 |    100% |           |
| main\_page\_generation/private\_page.py                       |       72 |       34 |     53% |89-90, 94-182, 186 |
| message\_factory/\_\_init\_\_.py                              |        0 |        0 |    100% |           |
| message\_factory/message\_factory.py                          |       67 |       49 |     27% |41-52, 57-58, 61-75, 84-108, 123-137 |
| metadata\_generators/\_\_init\_\_.py                          |        4 |        0 |    100% |           |
| metadata\_generators/extract\_emails.py                       |       49 |       16 |     67% |59, 64, 75, 86-103 |
| modules\_compilation/\_\_init\_\_.py                          |        0 |        0 |    100% |           |
| modules\_compilation/file\_hasher.py                          |       71 |        7 |     90% |93, 119-124 |
| parsers/\_\_init\_\_.py                                       |        0 |        0 |    100% |           |
| parsers/yang\_parser.py                                       |       85 |       29 |     66% |82, 90-98, 160-161, 165-168, 175-188, 228 |
| redis\_connections/\_\_init\_\_.py                            |        0 |        0 |    100% |           |
| redis\_connections/constants.py                               |        5 |        0 |    100% |           |
| redis\_connections/redis\_connection.py                       |       28 |        1 |     96% |        54 |
| redis\_connections/redis\_user\_notifications\_connection.py  |       13 |        5 |     62% | 17-24, 27 |
| rename\_file\_backup.py                                       |       47 |       10 |     79% | 68, 79-93 |
| tests/test\_check\_archived\_drafts.py                        |       92 |        3 |     97% |87-88, 188 |
| tests/test\_extract\_elem.py                                  |       29 |        1 |     97% |        89 |
| tests/test\_extract\_emails.py                                |       19 |        1 |     95% |        42 |
| tests/test\_file\_hasher.py                                   |       71 |        1 |     99% |        58 |
| tests/test\_gather\_ietf\_dependent\_modules.py               |       52 |        1 |     98% |        84 |
| tests/test\_get\_stats.py                                     |      106 |        3 |     97% |77-78, 214 |
| tests/test\_private\_page.py                                  |       30 |        0 |    100% |           |
| tests/test\_remove\_directory\_content.py                     |       53 |        1 |     98% |        93 |
| tests/test\_rename\_file\_backup.py                           |       49 |        1 |     98% |        92 |
| tests/test\_utility.py                                        |      135 |        0 |    100% |           |
| tests/test\_yang\_version\_1\_1.py                            |       37 |        1 |     97% |        67 |
| utility/\_\_init\_\_.py                                       |        0 |        0 |    100% |           |
| utility/static\_variables.py                                  |        3 |        0 |    100% |           |
| utility/utility.py                                            |      276 |       41 |     85% |79, 82, 112, 192, 194, 197-199, 216-217, 223-225, 228, 252, 267, 275-278, 283, 300, 305-306, 314, 316-327, 386, 392-394, 403 |
| versions.py                                                   |       28 |        0 |    100% |           |
|                                                     **TOTAL** | **2202** |  **364** | **83%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/YangCatalog/module-compilation/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/YangCatalog/module-compilation/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YangCatalog/module-compilation/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/YangCatalog/module-compilation/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FYangCatalog%2Fmodule-compilation%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/YangCatalog/module-compilation/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.