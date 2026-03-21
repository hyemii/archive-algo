// [코테] 부분 문자열의 최대 길이 - 중복 문자 제거
// Day 1 - Problem 1 | 2026.03.21
// 알고리즘 유형: 해시맵/슬라이딩 윈도우

import java.util.*;

public class Day1_1 {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        String s = scanner.nextLine();
        scanner.close();

        // 문자열 길이 체크
        if (s.length() < 1 || s.length() > 100000) {
            System.out.println("문자열 s의 길이는 1 ≤ s.length ≤ 100,000 입니다.");
            return;
        }

        // 유효한 문자로만 구성됐는지 체크
        for (char c : s.toCharArray()) {
            if (c < 32 || c > 126) {
                System.out.println("문자열은 영문 소문자, 대문자, 숫자, 공백, 특수문자로 구성됩니다.");
                return;
            }
        }

        List<Character> list = new ArrayList<>();
        for (char c : s.toCharArray()) {
            Character currentC = c;
            if (list.isEmpty() && list.size() == 0) {
                list.add(currentC);
                continue;
            }

            if (list.contains(currentC)) {
                int idx = list.indexOf(currentC);
                list = list.subList(idx, list.size() - 1);
            }
            
            list.add(currentC);
        }

        System.out.println("result: " + list.size());
    }
}
