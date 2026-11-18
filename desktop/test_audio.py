"""Build-time tests with no live server."""
import backend
def test():
    pcm = backend.ROGER_PCM
    assert len(pcm) == 3 * (5760 + 1440) * 2
    assert len(pcm) % 2 == 0  # PCM i16; last 20ms packet is padded in the capture loop
    assert any(pcm[:backend.MONO_BYTES])
    assert any(pcm[backend.MONO_BYTES * 8:backend.MONO_BYTES * 9])
    assert any(pcm[backend.MONO_BYTES * 16:backend.MONO_BYTES * 17])
    assert backend.key_label(None) == ""
    b = backend.Backend()
    assert b.client is not None
    assert not b.connected
    assert not b.test_roger()
    b.close()
    print("Windows Rust core, roger PCM and PTT tests: OK")

if __name__ == "__main__":
    test()
