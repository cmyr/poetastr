#poetastr

*poetastr* poetastr generates poems using tweets as lines, and streams these poems to a web browser. It also has its own twitter account, @pypoet, through which users can interact with it.

poetastr is still under development. Currently it consists of two components, a feeder and a simple web server. The feeder is the 'engine'; it consumes twitter data, handles the @pypoet twitter account, and publishes the raw stream, which is consumed by the web server. The web server handles the packaging and streaming of the raw feed to individual clients.

###Upcoming features:

- more variety in poems: poetastr's underlying engine, [poetryutils](https://www.github.com/cmyr/poetryutils2) is flexible, and can do a lot more. I'd like to include more poem types going forward.

- static site + site for individual poems: I want to have each poem get a permalink, and have a site that allows the exploration of previously generated poems.

- I want more integration with the twitter account, particularly the sharing of permalinks to relevant poems with people who have asked for a user to be included, for instance.