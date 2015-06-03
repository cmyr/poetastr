poet = {
			linesSeen: 0,
			poemsSeen: 0,
			poemSeenCounts: {
				_counts: Object(),
				countForPoemType: function( poemType )	{
					seen = this._counts[poemType]
					if (typeof(seen) == "undefined") {
						return 0
					} else {
						return seen
					}
				},

				sawPoemOfType: function ( poemType ) {
					poet.poemsSeen++;
					if (typeof(this._counts[poemType]) == "undefined") {
						this._counts[poemType] = 1
					} else {
						this._counts[poemType]++
					}
				}
			},

            recentLines : {
                maxLength: 15,
                add: function (item) {
                	poet.linesSeen++;
                    $('<p>'+item+'</p>').hide()
                    .prependTo('#recent-tweets')
                    .slideDown('fast');
                        if ($('#recent-tweets').children().length > this.maxLength) {
                            $('#recent-tweets p:last').slideDown('fast')
                            .remove();
                        }
                }
            },

            activeUsers: {
                users: Object(),
                addUser: function (user) {
                    user.color = randomColor()
                    user.remainingLines = user.filtered_count
                    this.users[user.screen_name] = user
                    document.styleSheets[0].cssRules[0].cssText = '.user-'+user.screen_name+' { color: '+user.color+ '};'
                },
                
                colorForUser: function (user) {
                    return this.users[user].color
                },

                sawLineForUser: function (user) {
                    this.users[user].remainingLines--
                }
            },

            formatLine: function (line) {
                var classes = 'poem-line'
                if (line.info.special_user != null) {
                    classes = classes+' user-line user-'+line.special_user
                }
                return '<div class="'+classes+'"><a class="line-link" href="'+line.info.id_str+'">'+line.info.text+'</a></div>'
            },

            formatPoem: function (poem) {
            	var title = '<h3>'+poem.poem_type+ ' '+this.poemSeenCounts.countForPoemType(poem.poem_type)+'</h3>'
                var lines = poem.lines.map(function(line) {
                        return poet.formatLine(line)
                        }).reduce(function(a, b) {
                            return a + b
                        });
                return '<div class="poem">'+title+lines+'</div>'
            },

            handleMessage: function (msg) {
                switch (msg.mtype) {
                    case "line":
                        this.recentLines.add(msg.body)
                        // $('#recent-tweets').html( this.recentLines.list.join('<br/>') )
                        break;
                    case "user-line":
                        this.recentLines.add(msg.body.text)
                        // $('#recent-tweets').html( this.recentLines.list.join('<br/>') )
                        console.log(msg)
                        this.activeUsers.sawLineForUser(msg.body.special_user)
                        break;
                    case "poem":
                    	this.poemSeenCounts.sawPoemOfType(msg.body.poem_type)
                        this.displayPoem(msg.body)
                        break;
                    case "track-user":
                        this.activeUsers.addUser(msg.body)
                        console.log('active users:')
                        console.log(this.activeUsers)
                        var formattedUser = '<div class="active-user user-'+msg.body.screen_name+'">'+msg.body.screen_name+'</div>'
                        $(formattedUser).hide()
                        .prependTo('.active-users')
                        .fadeIn('slow');
                        break;
                }
            },

            displayPoem: function (poem) {
                var formattedPoem = poet.formatPoem(poem)
                // formattedPoem.fadeIn(1000)
                switch (poem.poem_type) {
                    case "haiku":
                        $(formattedPoem).hide()
                        .prependTo('#left')
                        .slideDown('slow')

                        var length = $('#left').children().length;
                        console.log('haiku length: '+length)
                        if (length > 5) {
                            $('#left div.poem:last').fadeOut('slow')
                            .remove();
                        }
                        break;

                    case "limerick":
                        $(formattedPoem).hide()
                        .prependTo('#right')
                        .slideDown('slow')

                        var length = $('#right').length;
                        if (length > 3) {
                            $('#right:last-child').remove();
                        }
                        break;
                }
            }
        }