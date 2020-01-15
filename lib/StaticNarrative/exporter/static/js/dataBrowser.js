class DataBrowser {
    constructor(options) {
        this.dataFile = options.dataFile
        this.node = options.node
        this.loadData()
    }

    loadData() {
        fetch(this.dataFile)
            .then(data => data.json())
            .then(data => this.render(data))
            .catch(error => this.renderError(error))
    }

    renderError(error) {

    }

    render(data) {
        this.container = this.structureRender()
        this.node.appendChild(this.container)
        data.data.forEach((obj) => {
            let type = obj[2].split('-')[0].split('.')[1]
            new DataCard({
                container: this.container,
                data: obj,
                icon: data.types[type].icon
            })
        })
    }

    structureRender() {
        // do some stuff. make overall structure. I guess.
        let container = document.createElement('div')
        return container
    }
}

class DataCard {
    constructor(options) {
        this.data = options.data
        this.container = options.container
        this.icon = options.icon
        this.render()
    }

    render() {
        this.node = document.createElement('div')
        let iconNode = document.createElement('div')
        iconNode.innerHTML = `
            <span class="fa-stack fa-2x">
                <span class="fa fa-${this.icon.shape} fa-stack-2x" style="color: ${this.icon.color}"></span>
                <span class="fa fa-inverse fa-stack-1x ${this.icon.icon}"></span>
            </span>
        `;
        this.node.appendChild(iconNode)
        // this.node.innerHTML = this.data[1]
        this.container.appendChild(this.node)
        console.log(this.icon)
    }

}

/**
 * Converts a timestamp to a simple string.
 * Do this American style - HH:MM:SS MM/DD/YYYY
 *
 * @param {string} timestamp - a timestamp in number of milliseconds since the epoch, or any
 * ISO8601 format that new Date() can deal with.
 * @return {string} a human readable timestamp
 */
function readableTimestamp (timestamp) {
    if (!timestamp) {
        timestamp = 0;
    }
    var format = function (x) {
        if (x < 10)
            x = '0' + x;
        return x;
    };

    var d = parseDate(timestamp);
    var hours = format(d.getHours());
    var minutes = format(d.getMinutes());
    var seconds = format(d.getSeconds());
    var month = d.getMonth() + 1;
    var day = format(d.getDate());
    var year = d.getFullYear();

    return hours + ':' + minutes + ':' + seconds + ', ' + month + '/' + day + '/' + year;
}

/**
 * VERY simple date parser.
 * Returns a valid Date object if that time stamp's real.
 * Returns null otherwise.
 * @param {String} time - the timestamp to convert to a Date
 * @returns {Object} - a Date object or null if the timestamp's invalid.
 */
function parseDate (time) {
    /**
     * Some trickery here based on this StackOverflow post:
     * http://stackoverflow.com/questions/1353684/detecting-an-invalid-date-date-instance-in-javascript
     *
     * Try to make a new Date object.
     * If that fails, break it apart - This might be caused by some issues with the typical ISO
     * timestamp style in certain browsers' implementations. From breaking it apart, build a
     * new Date object directly.
     */
    var d = new Date(time);
    if (Object.prototype.toString.call(d) !== '[object Date]' || isNaN(d.getTime())) {
        var t = time.split(/[^0-9]/);
        // if t[0] is 0 or empty string, then just bail now and return null. This means that the
        // given timestamp was not valid.
        if (!t[0]) {
            return null;
        }
        while (t.length < 7) {
            t.push(0);
        }
        d = new Date(t[0], t[1]-1, t[2], t[3], t[4], t[5], t[6]);
        // Test the new Date object
        if (Object.prototype.toString.call(d) === '[object Date]') {
            // This would mean its got the 'Invalid Date' status.
            if (isNaN(d.getTime())) {
                return null;
            }
            else {
                d.setFullYear(t[0]);
                return d;
            }
        }
        return null;
    }
    else {
        return d;
    }
}
