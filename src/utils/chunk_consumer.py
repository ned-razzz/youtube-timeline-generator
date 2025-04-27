
class ChunkCunsumer:

	@staticmethod
	def consume_chunks(chunks):
		for idx, chunk in enumerate(chunks):
			print(f"[cosume: {idx}]")