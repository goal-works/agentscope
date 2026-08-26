import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("overview exposes seeded execution evidence", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Observe every decision.");
  await expect(page.getByText("6", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("66.7%", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Explore traces" })).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(5);
});

test("trace explorer filters error outcomes", async ({ page }) => {
  await page.goto("/traces");
  await page.getByLabel("Status").selectOption("error");
  await page.getByRole("button", { name: "Apply" }).click();

  await expect(page).toHaveURL(/status=error/);
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await expect(page.locator("tbody").getByText("error", { exact: true })).toHaveCount(2);
});

test("flagship trace detail preserves timeline payload and loop evidence", async ({ page }) => {
  await page.goto("/traces");
  await page.getByRole("link", { name: "Incident research — repeated search loop" }).click();

  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Incident research — repeated search loop",
  );
  await expect(page.getByText("Repeated identical tool call", { exact: true })).toBeVisible();
  await expect(page.locator(".timeline .event")).toHaveCount(9);
  await page.getByText("Inspect payload", { exact: true }).first().click();
  await expect(page.locator(".event pre").first()).toBeVisible();
});

test("trace comparison renders two durable executions", async ({ page }) => {
  await page.goto("/compare");

  await expect(page.locator(".compare-column")).toHaveCount(2);
  await expect(page.getByText("Latency delta", { exact: true })).toBeVisible();
  await expect(page.getByText("Final result", { exact: true })).toHaveCount(2);
});

for (const route of ["/", "/traces", "/compare", "/diagnostics", "/documentation"] as const) {
  test(`${route} has no serious or critical accessibility violations`, async ({ page }) => {
    await page.goto(route);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    const serious = results.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact ?? ""),
    );
    expect(serious).toEqual([]);
  });
}
