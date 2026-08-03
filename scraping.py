import datetime
import time

from playwright.sync_api import sync_playwright, ViewportSize, Page

URL = "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=43&tm2lIdx=4306000000&tm3lIdx=4306080000"


def attach_debug_handlers(page):
    page.on("console", lambda m: print(f"CONSOLE [{m.type}] {m.text}"))
    page.on("pageerror", lambda e: print(f"PAGEERROR {e.message}"))
    page.on("requestfailed", lambda r: print(f"FAILED {r.url} {r.failure}"))

    def on_response(r):
        if r.request.is_navigation_request():
            via = " (redirected)" if r.request.redirected_from else ""
            print(f"RESP {r.status} {r.url}{via}")

    page.on("response", on_response)

    def on_xhr_request(r):
        if r.resource_type in ("xhr", "fetch"):
            print(f">>> {r.method} {r.url}")
            if r.post_data:
                print(f"    POST: {r.post_data[:800]}")

    page.on("request", on_xhr_request)

    def on_xhr_response(r):
        if r.request.resource_type in ("xhr", "fetch"):
            print(f"<<< {r.status} {r.url}")
            try:
                print(f"    BODY: {r.text()[:1500]}")
            except Exception as e:
                print(f"    (본문 없음) {type(e).__name__}")

    page.on("response", on_xhr_response)


def dump_frames(page: Page):
    for f in page.frames:
        print(f"name={f.name!r}  url={f.url}")


def scraping(b_no_list: list[str]) -> list[dict]:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir="",
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
            viewport=ViewportSize({"width": 1920, "height": 1080}),
        )

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # attach_debug_handlers(page)

        page.goto(URL)
        print('Page moved')
        page.wait_for_load_state("networkidle")
        dump_frames(page)
        print('Frames loaded')

        result = []
        total = len(b_no_list)
        print(f'TOTAL: {total}')
        for b_no in b_no_list:
            try:
                page.fill("input#mf_txppWframe_bsno", b_no)
                page.click("#mf_txppWframe_trigger5")
                page.wait_for_timeout(2000)
                result.append(
                    {
                        "biz_num": b_no,
                        "status": parse_status(page.locator('td[id="mf_txppWframe_grid2_cell_0_1"]').inner_text()),
                        "date": page.locator('td[id="mf_txppWframe_grid2_cell_0_2"]').inner_text(),
                    }
                )
            except Exception as e:
                result.append((b_no, f"ERROR: {str(e)[:64]}"))

            if len(result) % 10 == 0:
                print(f"PROCESSED: {len(result)} / {total}")

            time.sleep(1)

        ctx.close()

    print(f'COMPLETE: {len(result)} / {total}')
    return result

def parse_status(status: str) -> str:
    if status.startswith('부가가치세'):
        return status.split(' ')[1]
    elif '등록되지 않은' in status:
        return '미등록'

    return status

def main(filename: str) -> None:
    input_path = f'/app/files/input/{filename}'
    with open(input_path, 'r', encoding='utf-8') as f:
        b_no_list = f.read()

    result = scraping(b_no_list.split(','))
    today = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    with open(f'/app/files/output/result_{len(result)}_{today}.csv', 'w', encoding='utf-8') as f:
        f.write('biz_num,status,date\n')
        for r in result:
            f.write(f'{r["biz_num"]},{r["status"]},{r["date"]}\n')


if __name__ == "__main__":
    main('input.txt')