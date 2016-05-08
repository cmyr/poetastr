poet = {
    _window: null,
    windowLoaded: function (wndw) {
        this._window = wndw;
    },
	linesSeen: 0,
	poemsSeen: 0,
	poemSeenCounts: {
		_counts: {},
		countForPoemType: function ( poemType )	{
			seen = this._counts[poemType];
			if (typeof(seen) == "undefined") {
				return 0;
			} else {
				return seen;
			}
		},

		sawPoemOfType: function ( poemType ) {
			poet.poemsSeen++;
			if (typeof(this._counts[poemType]) == "undefined") {
				this._counts[poemType] = 1;
			} else {
				this._counts[poemType]++;
			}
		}
	},
    showLangs: {
        'en': false,
        'fr': true
    },

    _lang: 0,
    langToggle: function () {
        this._lang = (this._lang + 1) % 3
        var newText = '';
        switch (this._lang) {
            case 0:
                poet.showLangs['en'] = false;
                newText = 'FR';
                if (this.recentPoems['fr'] !== null) {
                    this.displayPoem(this.recentPoems['fr']);
                }
                break;
            case 1:
                poet.showLangs['fr'] = false;
                poet.showLangs['en'] = true;
                newText = 'EN';
                if (this.recentPoems['en'] !== null) {
                    this.displayPoem(this.recentPoems['en']);
                }
                break;
            default:
                poet.showLangs['fr'] = true;
                newText = 'FR   / EN';
                break;
        }

        var el = $('#lang-select').fadeOut('fast', function() {
            $(this).html(newText)
            .fadeIn('fast');
        });
    },

    formatLine: function (line) {
        var classes = 'poem-line';
        var username = "";
        if (line.info.special_user != null) {
            classes = classes+' user-line user-'+line.info.special_user;
            username = '— @'+line.info.special_user;
        }
        return '<div class="'+classes+'">'+
        '<a class="line-link" link="'+line.info.id_str+'" href="#" onclick="javascript:tweetClicked(\''+line.info.id_str+'\')">'+line.info.text+
        '</a>'+'<span class="user-name">'+username+'</span>'+'</div>';
    },

    formatPoem: function (poem) {
    	var title = '<h3>'+poem.poem_type+ ' '+this.poemSeenCounts.countForPoemType(poem.poem_type)+'</h3>';
        var lines = poem.lines.map(function(line) {
                return poet.formatLine(line);
                }).reduce(function(a, b) {
                    return a + b;
                });
        return '<div class="poem-frame"><div class="poem">'+title+lines+'</div></div>';
    },

    handleMessage: function (msg) {
        switch (msg.mtype) {
            case "poem":
            	this.poemSeenCounts.sawPoemOfType(msg.body.poem_type);
                this.addPoem(msg.body);
                break;
            case "rate-limit":
                console.log('rate limited');
                console.log(msg.body.wait_time);
                break;
            case "keep_alive":
                break;
            default:
            console.log(msg.type)
        }
    },

    recentPoems: {
        'en': null,
        'fr': null
    },
    
    waitingForPoem: true,
    poemQueue: Array(),
    addPoem: function (poem) {
        this.poemCallback();
        if (this.waitingForPoem && this.showLangs[poem.lang]) {
            this.displayPoem(poem);
        } else {
            this.poemQueue.push(poem);   
            console.log('enqued poem, total poems = '+this.poemQueue.length);
        }
    },
    
    displayPoem: function (poem) {
        this.waitingForPoem = false;
        this.recentPoems[poem.lang] = poem;
        var container = document.getElementById("main-container");

        var formattedPoem = poet.formatPoem(poem);
        $('#sole-poem-container').fadeOut(4000, function() {
            $(this).html('')
            .hide()
            .html(formattedPoem)
            .fadeIn(1000, function() {
                setTimeout(function() {
                    poet.displayFinished();
                },
                8000)
            });
        });
    },

    displayFinished: function() {
        var next = this.poemQueue.find(function(poem) {
            return this.showLangs[poem.lang]
        },
        poet)

        if (next) {
            this.poemQueue.splice(this.poemQueue.indexOf(next), 1);
            this.displayPoem(next);
        } else {
            this.waitingForPoem = true;
            console.log('waiting for poem')
        }
    },

    poemCallback: function() {
        console.log('sending callback')
        $.get('/client_wrote_poem', {param1: 'value1'}, function(data, textStatus, xhr) {
          // console.log('client wrote poem success');
        })
    }
};


tweetClicked = function(tweet_id) {
    var container = document.getElementById('embedded-tweets');
    var newNode = document.createElement('div');
    newNode.id = tweet_id;
    newNode.className = 'twitter-embed';
    container.insertBefore(newNode, container.firstChild);

    
    poet._window.twttr.widgets.createTweet(
        tweet_id,
        newNode,

        {
            cards: 'hidden',
            dnt: true,
            // width: 300,
            omit_script: true
        }).then( function(el) {
            $(newNode).animate({ opacity: 1.0 }, 'slow')
            .delay(7000)
            .slideToggle('slow', function() {
                $(this).remove();
            })
         });
}
