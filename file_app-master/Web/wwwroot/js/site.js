'use strict';

webix.ready(function () {

    webix.ui({
        view: "filemanager",
        ready: function () {
            this.getMenu().add({
                id: "download",
                icon: "webix_icon fa-download",
                value: "Download",
                batch: "file"
            }, 0);
        },
        id: "files",
        handlers: {
            "download": "api/download",
            "upload": "api/upload",
            "remove": "api/remove",
            "rename": "api/rename",
            "create": "api/create",
            "copy": "api/copy"
        },
        on: {
            'onViewInit': function (name, config) {
                if (name === 'table') {
                    // an array with columns configuration
                    var columns = config.columns;
                    // configuration of a new column
                    var sizeIndex = -1;

                    for (var i = 0; i < columns.length; i++) {
                        if (columns[i].header === 'Size') {
                            sizeIndex = i;
                            break;
                        }
                    }

                    if (sizeIndex > -1) {
                        columns.splice(sizeIndex, 1)
                    }

                    var advancedSizeColumn = {
                        id: 'advancedSize',
                        header: 'Size',
                        fillspace: 1,
                        template: function (obj) {
                            var value = obj.size;
                            var isInt = (parseInt(value, 10) === value);

                            // get size label
                            var labels = webix.i18n.filemanager.sizeLabels; // ["B","KB",...]
                            var sizeIndex = 0;

                            while (value / 1024 > 1) {
                                value = value / 1024;
                                sizeIndex++;
                            }
                            var label = labels[sizeIndex];

                            // locale format
                            var getFormattedValue = webix.Number.numToStr({
                                decimalDelimiter: webix.i18n.decimalDelimiter,
                                groupDelimiter: webix.i18n.groupDelimiter,
                                decimalSize: isInt ? 0 : webix.i18n.groupSize
                            });

                            return getFormattedValue(value) + "" + label;
                        }
                    };
                    // insert a column
                    webix.toArray(columns).push(advancedSizeColumn);
                }
            }
        }
    });

    $$("files").load("api/data");
});
