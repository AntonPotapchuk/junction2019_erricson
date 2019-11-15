'use strict';

const visualsConfig = {
// @serverAddr: Address of the server to connect to, eg. 'http://localhost:8000'
//              If empty, uses the same server the visualization is hosted on.
    serverAddr: "http://localhost:8080",
    updateInterval: 1000, // ms
    resolution: {
        x: 1280,
        y: 1100,
    },
};

const TILE_WIDTH = 30;

// maps passability to the tiles in dirt.png
const CITY_TILE_INDEXES = {
    passable: 0,
    impassable: 1,
};

class ChallengeScene extends Phaser.Scene {
    constructor(config) {
        // this is some information for phaser about our scene
        const sceneConfig = {
            key: "challenge-scene",
        };

        super(sceneConfig);

        this.config = config;

        this.cityConfig = {
            width: null,
            height: null,
        };

        this.data = {
            lastUpdate: 0,
            updating: false,
            city: null, // this will hold the latest data retrieved from server
        };

        this.map = null;
    }

    preload() {
        this.load.image('city-tiles', 'assets/elements.png');
        //this.load.image('car', 'assets/car_spr.png');

        // We need to retrieve the world once from the server to know the city
        // size before we can continue. I'll do it synchronously because that's
        // the easiest. It stalls rendering, which isn't cool, but this is only
        // going to happen during the loading phase so probably nobody notices.
        this.retrieveCityConfig();
    }

    async retrieveCityConfig() {
        // This synchronously retrieves the game state once. Don't call after
        // the loading phase as this stalls rendering.

        const worldApi = `${this.config.serverAddr}/api/v1/world`;

        const resp = await fetch(worldApi);

        const data = await resp.json();

        console.debug("initial game state", data);

        this.cityConfig = {
            width: data.width,
            height: data.height,
        };
    }

    create() {
        this.map = this.make.tilemap({
            width: this.cityConfig.width,
            height: this.cityConfig.height,
            tileWidth: TILE_WIDTH,
            tileHeight: TILE_WIDTH,
        });

        const tiles = this.map.addTilesetImage("city-tiles");

        const cityLayer = this.map.createBlankDynamicLayer("city-layer", tiles);

        // fit to screen and center

        const cityWidth = this.config.resolution.y;

        cityLayer.setDisplaySize(cityWidth, cityWidth);

        this.cameras.main.setScroll(
            -(this.config.resolution.x / 2) + (cityWidth / 2),
            0);
    }

    getCityGridTiles(grid) {
        function getCityGridTile(node) {
            if (node) {
                return CITY_TILE_INDEXES["passable"];
            }
            return CITY_TILE_INDEXES["impassable"];
        }

        return grid.map(getCityGridTile);
    }

    getCustomerGridTiles(customers, grid) {
        function getCustomerPosition(customer) {
            if (customer.status == "waiting") {
                return customer.origin;
            } else if (customer.status == "delivered")  {
                return customer.destination;
            } else {
                return;
            }
        }
        for (var key in customers) {
            if (getCustomerPosition(customers[key])) {
                grid[getCustomerPosition(customers[key])] = 2;
            }
        }
        return grid;
    }

    getCarGridTiles(cars, grid) {
        for (var key in cars) {
            grid[cars[key].position] = 3 + cars[key].team_id;
        }
        return grid;
    }

    update(time, delta) {
        if (this.shouldUpdateData(time)) {
            this.data.lastUpdate = time;
            this.updateData();
        }

        // hacky... don't try to draw the game if we don't have data yet
        if (!this.data.city) {
            return;
        }

        this.updateCityGrid();
    }

    updateCityGrid() {
        var gridTiles = this.getCityGridTiles(this.data.city.grid);
        gridTiles = this.getCustomerGridTiles(this.data.city.customers, gridTiles)
        gridTiles = this.getCarGridTiles(this.data.city.cars, gridTiles)

        // phaser wants to read the tile grid as an array-of-arrays...
        const tiles = this.gridToArrays(gridTiles, this.cityConfig.width);

        this.map.putTilesAt(tiles, 0, 0, false, "city-layer");
    }

    gridToArrays(grid, width) {
        let arrays = [];
        let acc = [];
        for (let i = 0; i < grid.length; ++i) {
            acc.push(grid[i]);
            if (acc.length === width) {
                arrays.unshift(acc);
                acc = [];
            }
        }
        return arrays;
    }

    shouldUpdateData(currentTime) {
        if (this.data.updating) {
            // a previous fetch is already pending!
            return false;
        }

        // no more often than once per updateInterval
        if (currentTime < this.data.lastUpdate + this.config.updateInterval) {
            return false;
        }

        return true;
    }

    updateData() {
        this.data.updating = true;

        const worldApi = `${this.config.serverAddr}/api/v1/world`;

        fetch(worldApi).then(this.dataUpdateHandleResponse.bind(this));
    }

    // callback
    dataUpdateHandleResponse(response) {
        // Reading a HTTP fetch response body is also an asynchronous operation.
        // Therefore a second callback is set up.
        response.json().then(this.dataUpdateReadData.bind(this));
    }

    // callback
    dataUpdateReadData(data) {
        // at this point we have the data finally available
        this.data.city = data;
        this.data.updating = false;
    }
}

const phaserConfig = {
    type: Phaser.AUTO,
    width: visualsConfig.resolution.x,
    height: visualsConfig.resolution.y,
    physics: {
        default: 'arcade',
        arcade: {
            debug: true     // TODO
        }
    },
    scene: [new ChallengeScene(visualsConfig)],
};

const game = new Phaser.Game(phaserConfig);
