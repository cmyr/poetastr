poet = {    
            _window: null,
            windowLoaded: function (wndw) {
                this._window = wndw;
                $('#sole-poem-container').click( function(event) {
                            poet.shouldDisplay = false;
                            $('#sole-poem-container').stop()
                            .fadeIn('fast');
                            poet._window.setTimeout(function() {
                                poet.shouldDisplay = true;
                                
                            },
                            5000)
                        });
            },

			linesSeen: 0,
			poemsSeen: 0,
            // activeUsers: 0,
			poemSeenCounts: {
				_counts: {},
				countForPoemType: function( poemType )	{
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
                'en': true,
                'fr': true
            },

            langSelect: function ( lang ) {
                var elementID = (lang == 'en') ? '#lang-en' : '#lang-fr';
                var toggle = false;
                
                poet.showLangs[lang] = !poet.showLangs[lang];

                if (!poet.showLangs['en'] && !poet.showLangs['fr']) {
                    toggle = true;
                }

                if (poet.showLangs[lang] == true) {
                    $(elementID).addClass('active');
                    if (this.recentPoems[lang] !== null) {
                        this.displayPoem(this.recentPoems[lang]);
                    }
                } else {
                    $(elementID).removeClass('active');
                }

                if (toggle) {
                    var otherLang = (lang == 'en') ? 'fr' : 'en';
                    poet.langSelect(otherLang)                    
                }

            },

            formatLine: function (line) {
                var classes = 'poem-line';
                var username = "";
                if (line.info.special_user != null) {
                    classes = classes+' user-line user-'+line.info.special_user;
                    username = '— @'+line.info.special_user;
                }
                return '<div class="'+classes+'">'+
                '<a class="line-link" link="'+line.info.id_str+'" href="#">'+line.info.text+
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
                    case "line":
                        // this.recentTweets.add(msg.body);
                        break;
                    case "user-line":
                        // this.recentLines.add(msg.body.text);
                        // this.activeUsers.sawLineForUser(msg.body.special_user);
                        break;
                    case "poem":
                    	this.poemSeenCounts.sawPoemOfType(msg.body.poem_type);
                        this.addPoem(msg.body);
                        break;
                    case "track-user":
                        // this.activeUsers.addUser(msg.body);
                        this.showNewActiveUser(msg.body);
                        console.log(msg.body.screen_name);
                        break;
                    case "rate-limit":
                        console.log('rate limited');
                        console.log(msg.body.wait_time);
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
                console.log('added poem')
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
                        console.log('set timeout');
                        setTimeout(function() {
                            console.log('timeout finished');
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


            activeUsers: {
            	_userCount: 0,
            	increment: function () {
            		this._userCount++;
            		if (this._userCount == 1) {
            			// show element
            			console.log('toggling on?');
            			$('.active-users').slideToggle();
            		}
            	},
            	decrement: function () {
            		this._userCount--;
            		if (this._userCount === 0) {
            			// show element
            			$('.active-users').slideToggle();
            			console.log('toggling off?');
            		}
            	}
            },

            showNewActiveUser: function (newUser) {
            	var formattedUser = '<div class="active-user"><span>@'+newUser.screen_name+'</span></div>';
            	
            	this.activeUsers.increment();
            	$(formattedUser).hide()
            	.appendTo('.active-users')
            	.fadeIn('slow')
            	.delay(60000)
            	.fadeOut('slow', function() {
            		$(this).remove();
            		poet.activeUsers.decrement();
            	});
            }
    }



            // recentTweets: {
            //     maxLength: 20,
            //     add: function(item) {
            //         poet.linesSeen++;
            //         var newTweet = $('<div class="twitter-embed" id="'+item.id_str+'"></div>').hide()
            //         .prependTo('#recent-tweets')
            //         poet._window.twttr.widgets.createTweet(
            //             item.id_str,
            //             document.getElementById(item.id_str),
            //             {
            //                 cards: 'hidden',
            //                 dnt: true,
            //                 width: poet._tweetWidth,
            //                 omit_script: true
            //             }).then( function (elem) {
            //                 newTweet.slideDown('fast');
            //             });

            //         if ($('#recent-tweets').children().length > this.maxLength) {
            //             $('#recent-tweets div:last').slideDown('fast')
            //             .remove();
            //         }
            //     }
            // },
