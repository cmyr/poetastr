poet = {
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
                } else {
                    $(elementID).removeClass('active');
                }

                if (toggle) {
                    var otherLang = (lang == 'en') ? 'fr' : 'en';
                    poet.langSelect(otherLang)                    
                }
            },

            recentLines: {
                maxLength: 15,
                add: function (item) {
                	poet.linesSeen++;
                	$('#tweets-seen span').html(poet.linesSeen);
                    $('<p>'+item+'</p>').hide()
                    .prependTo('#recent-tweets')
                    .slideDown('fast');
                        if ($('#recent-tweets').children().length > this.maxLength) {
                            $('#recent-tweets p:last').slideDown('fast')
                            .remove();
                        }
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
                        this.recentLines.add(msg.body);
                        break;
                    case "user-line":
                        this.recentLines.add(msg.body.text);
                        // this.activeUsers.sawLineForUser(msg.body.special_user);
                        break;
                    case "poem":
                    	this.poemSeenCounts.sawPoemOfType(msg.body.poem_type);
                        this.displayPoem(msg.body);
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

            displayPoem: function (poem) {
                if (poet.showLangs[poem.lang]) {
                    // if we receive items too quickly we can miss removals and then they pile up
                    var container = document.getElementById("main-container");
                    while (container.children.length > 1 ) {
                        container.removeChild(container.lastChild);
                        console.log('removed extra child', container.children.length)
                   }

                    var formattedPoem = poet.formatPoem(poem);
                    $(formattedPoem).hide()
                    .prependTo('#main-container')
                    .slideDown('slow')
                    .promise().always( function() {
                        if ($('#main-container').children().length > 1) {
                            $('#main-container div.poem:last').fadeOut('slow')
                            .promise().always( function() {
                                $(this).remove();
                            });
                        }
                    });
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
        };