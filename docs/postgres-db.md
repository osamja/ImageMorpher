I'm wondering if a Postgres sql db will be useful for MyMorph.  If we had a database, we could

- Morph States
	- keep a record of all the images the user morphed.  Show the status of the morphed image.  Processing, Done, Deleted.  We could also show when the morph is going to be auto-deleted
- User record of past morphs
- Store their push token


Morph Model
	ID (Hash filename):
	Created_at: timestamp
	user_id: integer
	status: <None, Processing, Done, Expired> could be an enum
	is_supermorph: bool
	client: ios_mymorph
	morphed_url: 
	src_img1: 
	src_img2: 
	


