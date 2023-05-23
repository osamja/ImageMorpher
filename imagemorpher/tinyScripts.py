# Print the number of completed and failed jobs.

morphs = Morph.objects.all().filter(is_morph_sequence=True)

num_completed = 0
num_failed = 0

for morph in morphs:
	if morph.status == 'complete':
		num_completed += 1
	elif morph.status == 'failed':
		num_failed += 1

print(num_completed, num_failed, len(morphs))

