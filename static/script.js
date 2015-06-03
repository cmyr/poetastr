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
                return '<div class="poem">'+title+lines+'</div>';
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
                }
            },

            displayPoem: function (poem) {
                var formattedPoem = poet.formatPoem(poem);
                switch (poem.poem_type) {
                    case "haiku":
                        $(formattedPoem).hide()
                        .prependTo('#left')
                        .slideDown('slow');

                        if ($('#left').children().length > 5) {
                            $('#left div.poem:last').fadeOut('slow')
                            .remove();
                        }
                        break;

                    case "limerick":
                        $(formattedPoem).hide()
                        .prependTo('#right')
                        .slideDown('slow');

                        if ($('#right').children().length > 3) {
                            $('#right div.poem:last').fadeOut('slow')
                            .remove();
                        }
                        break;
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