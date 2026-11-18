import io

from PIL import Image
from pytest_bdd import given, parsers, scenarios, then, when

from support import capture, png_bytes
from wallpaper import image_post

scenarios("features/image.feature")


@given(parsers.parse("{width:d}x{height:d} PNG 이미지"), target_fixture="raw")
def _plain(width, height):
    return png_bytes(width, height)


@given("가로 3등분(빨강, 초록, 파랑)된 1200x400 PNG 이미지", target_fixture="raw")
def _three_bands():
    image = Image.new("RGB", (1200, 400))
    for index, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        image.paste(color, (index * 400, 0, (index + 1) * 400, 400))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("투명 배경 RGBA PNG 이미지", target_fixture="raw")
def _transparent():
    return png_bytes(300, 600, color=(10, 20, 30, 0), mode="RGBA")


@given("이미지가 아닌 바이트", target_fixture="raw")
def _not_an_image():
    return b"definitely not an image"


@when(parsers.parse("{width:d}x{height:d} 크기로 변환한다"))
def _convert(raw, ctx, width, height):
    ctx["result"], ctx["error"] = capture(image_post.to_wallpaper, raw, width, height)


@then(parsers.parse("결과는 {width:d}x{height:d} JPEG 이다"))
def _is_jpeg(ctx, width, height):
    assert ctx["error"] is None
    with Image.open(io.BytesIO(ctx["result"])) as image:
        assert image.format == "JPEG"
        assert image.size == (width, height)


@then("결과의 가운데 픽셀은 초록색 계열이다")
def _center_is_green(ctx):
    with Image.open(io.BytesIO(ctx["result"])) as image:
        red, green, blue = image.convert("RGB").getpixel((image.width // 2, image.height // 2))
    assert green > 150 and red < 100 and blue < 100


@then("이미지 처리 오류가 발생한다")
def _processing_error(ctx):
    assert isinstance(ctx["error"], image_post.ImageProcessingError)
